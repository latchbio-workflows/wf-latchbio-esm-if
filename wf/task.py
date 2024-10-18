import functools
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from flytekit import task
from flytekitplugins.pod import Pod
from kubernetes.client.models import (
    V1Container,
    V1SecurityContext,
)
from latch.executions import rename_current_execution
from latch.functions.messages import message
from latch.resources.tasks import (
    _get_large_gpu_pod,
    _get_small_gpu_pod,
    get_v100_x1_pod,
)
from latch.types.directory import LatchOutputDir
from latch.types.file import LatchFile

sys.stdout.reconfigure(line_buffering=True)


def _add_privileged(x: Pod):
    containers = x.pod_spec.containers
    assert containers is not None
    assert len(containers) > 0
    container: V1Container = containers[0]

    container.security_context = V1SecurityContext(privileged=True)

    return x


privileged_large_gpu_task = functools.partial(
    task, task_config=_add_privileged(_get_large_gpu_pod())
)

privileged_small_gpu_task = functools.partial(
    task, task_config=_add_privileged(_get_small_gpu_pod())
)

privileged_v100_x1_gpu_task = functools.partial(
    task, task_config=_add_privileged(get_v100_x1_pod())
)


@privileged_small_gpu_task(cache=True)
def esmif_task(
    run_name: str,
    input_pdb: LatchFile,
    output_directory: LatchOutputDir,
    chain: Optional[str] = None,
    temperature: float = 1.0,
    num_samples: int = 1,
    multichain_backbone: bool = False,
    nogpu: bool = False,
) -> LatchOutputDir:
    rename_current_execution(str(run_name))

    print("-" * 60)
    print("Creating local directories")
    local_output_dir = Path(f"/root/outputs/{run_name}")
    local_output_dir.mkdir(parents=True, exist_ok=True)

    print("-" * 60)
    subprocess.run(["nvidia-smi"], check=True)
    subprocess.run(["nvcc", "--version"], check=True)

    print("-" * 60)
    print("Mounting ObjectiveFS")
    ofs_p = Path("ofs").resolve()
    ofs_p.mkdir(parents=True, exist_ok=True)

    mount_command = [
        "mount.objectivefs",
        "-o",
        "mtplus,noatime,nodiratime,noratelimit,freebw,hpc",
        "s3://objectivefs-proteintools/esm",
        str(ofs_p),
    ]

    subprocess.run(mount_command, check=True)

    max_wait_time = 15
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        if any(ofs_p.iterdir()):
            print("ObjectiveFS mounted successfully")
            break
        time.sleep(1)
    else:
        print("Error: ObjectiveFS mount timed out")
        message("error", {"title": "ObjectiveFS Mount failed", "body": "Failed mount"})
        sys.exit(1)

    print("-" * 60)
    print("Linking databases")
    checkpoints_dir = Path("/root/.cache/torch/hub/")
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    symlinks = [("esm_models", "checkpoints")]

    print("Creating symlinks...")
    for source, target in symlinks:
        source_path = ofs_p / source
        target_path = checkpoints_dir / target

        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.symlink_to(source_path)
            print(f"  Created: {target_path} -> {source_path}")

    print("Symlink creation complete.")

    print("-" * 60)
    print("Running Evolutionary Scale Modeling (ESM) Inverse Folding")
    esm_dir = Path("/root/esm")
    outpath = local_output_dir / f"{run_name}.fasta"

    command = [
        "python",
        "examples/inverse_folding/sample_sequences.py",
        str(input_pdb.local_path),
        "--outpath",
        str(outpath),
        "--temperature",
        str(temperature),
        "--num-samples",
        str(num_samples),
    ]

    if chain:
        command.extend(["--chain", chain])
    if multichain_backbone:
        command.append("--multichain-backbone")
    else:
        command.append("--singlechain-backbone")
    if nogpu:
        command.append("--nogpu")

    print(f"Running prediction command: {' '.join(command)}")

    try:
        subprocess.run(command, cwd=esm_dir)
        print("Done")
    except Exception as e:
        print("FAILED: Predicing sequences")
        message("error", {"title": "ESMFold Inverse Folding failed", "body": f"{e}"})
        sys.exit(1)

    print("-" * 60)
    print("Scoring sequences")
    score_outpath = local_output_dir / f"{run_name}_scores.csv"

    score_command = [
        "python",
        "examples/inverse_folding/score_log_likelihoods.py",
        str(input_pdb.local_path),
        str(outpath),
        "--outpath",
        str(score_outpath),
    ]

    if chain:
        score_command.extend(["--chain", chain])

    if multichain_backbone:
        score_command.append("--multichain-backbone")
    else:
        score_command.append("--singlechain-backbone")

    print(f"Running scoring command: {' '.join(score_command)}")

    try:
        subprocess.run(
            score_command,
            cwd=esm_dir,
            check=True,
        )
        print("Scoring sequences completed successfully")
    except Exception as e:
        print("FAILED: Scoring sequences")
        message("error", {"title": "ESMFold Scoring failed", "body": f"{e}"})
        sys.exit(1)

    print("-" * 60)
    print("Returning results")
    return LatchOutputDir(str("/root/outputs"), output_directory.remote_path)
