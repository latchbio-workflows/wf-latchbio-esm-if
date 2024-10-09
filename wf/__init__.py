from typing import Optional

from latch.resources.launch_plan import LaunchPlan
from latch.resources.workflow import workflow
from latch.types.directory import LatchOutputDir
from latch.types.file import LatchFile
from latch.types.metadata import (
    LatchAuthor,
    LatchMetadata,
    LatchParameter,
    LatchRule,
    Params,
    Section,
    Spoiler,
    Text,
)

from wf.task import esmif_task

flow = [
    Section(
        "Input",
        Params(
            "input_pdb",
            "chain",
            "num_samples",
            "multichain_backbone",
        ),
        Spoiler(
            "Computation Settings",
            Params(
                "temperature",
                "nogpu",
            ),
        ),
    ),
    Section(
        "Output",
        Params("run_name"),
        Text("Directory for outputs"),
        Params("output_directory"),
    ),
]


metadata = LatchMetadata(
    display_name="Evolutionary Scale Modeling Inverse Folding",
    author=LatchAuthor(
        name="Meta AI Research",
    ),
    repository="https://github.com/facebookresearch/esm",
    license="MIT",
    tags=["Protein Engineering"],
    parameters={
        "run_name": LatchParameter(
            display_name="Run Name",
            description="Name of run",
            batch_table_column=True,
            rules=[
                LatchRule(
                    regex=r"^[a-zA-Z0-9_-]+$",
                    message="Run name must contain only letters, digits, underscores, and dashes. No spaces are allowed.",
                )
            ],
        ),
        "input_pdb": LatchParameter(
            display_name="Input PDB File",
            description="Input PDB file for inverse folding",
            batch_table_column=True,
        ),
        "output_directory": LatchParameter(
            display_name="Output Directory",
            description="Directory to store output files",
            batch_table_column=True,
        ),
        "chain": LatchParameter(
            display_name="Chain ID",
            description="Chain ID for the chain of interest (default: None)",
            batch_table_column=True,
        ),
        "temperature": LatchParameter(
            display_name="Temperature",
            description="Temperature for sampling, higher for more diversity (default: 1.0)",
            batch_table_column=True,
        ),
        "num_samples": LatchParameter(
            display_name="Number of Samples",
            description="Number of sequences to sample (default: 1)",
            batch_table_column=True,
        ),
        "multichain_backbone": LatchParameter(
            display_name="Use Multichain Backbone",
            description="Use the backbones of all chains in the input for conditioning (default: False)",
            batch_table_column=True,
        ),
        "nogpu": LatchParameter(
            display_name="No GPU",
            description="Do not use GPU even if available (default: False)",
            batch_table_column=True,
        ),
    },
    flow=flow,
)


@workflow(metadata)
def esmif_workflow(
    run_name: str,
    input_pdb: LatchFile,
    output_directory: LatchOutputDir = LatchOutputDir("latch:///ESMInverseFolding"),
    chain: Optional[str] = None,
    temperature: float = 1.0,
    num_samples: int = 1,
    multichain_backbone: bool = False,
    nogpu: bool = False,
) -> LatchOutputDir:
    return esmif_task(
        run_name=run_name,
        input_pdb=input_pdb,
        output_directory=output_directory,
        chain=chain,
        temperature=temperature,
        num_samples=num_samples,
        multichain_backbone=multichain_backbone,
        nogpu=nogpu,
    )


LaunchPlan(
    esmif_workflow,
    "Inverse Folding Test",
    {
        "run_name": "Test_Run",
        "input_pdb": LatchFile(
            "s3://latch-public/proteinengineering/esm/inversefolding/5YH2.pdb"
        ),
        "chain": "C",
        "num_samples": 5,
    },
)
