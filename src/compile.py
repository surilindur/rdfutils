"""
Command for compiling RDF data from multiple files into a single document,
with the option of processing the data using SPARQL queries before serialization.
"""

from hashlib import sha256
from pathlib import Path
from os.path import splitext

from typer import Typer
from typer import Option

from rdflib.term import URIRef
from rdflib.term import Literal
from rdflib.graph import Graph
from rdflib.graph import Dataset
from rdflib.void import generateVoID

from typing_extensions import Annotated

from utils import uri
from utils import path
from utils import iterate_files
from utils import FILE_URI_PREFIX
from utils import RDF_EXTENSIONS
from utils import SPARQL_EXTENSIONS
from utils import SerializationFormat

module = Typer()


def load_data(root: Path, graph: URIRef) -> Dataset:
    """Load all data from files in the specified path."""

    dataset = Dataset(default_union=True)
    dataset_graph = dataset.graph(identifier=graph)

    for file_path in iterate_files(root=root, extensions=RDF_EXTENSIONS):
        print(f"Parsing <{file_path.as_uri()}>")

        # Determine relative path
        file_uri = file_path.relative_to(root).as_posix()

        # Remove extension
        file_uri = file_uri.rsplit(".", 1)[0]

        # Move .../index to .../
        file_uri = file_uri.removesuffix("index").removesuffix("/")

        if graph.endswith(":"):
            file_uri = URIRef(f"{graph}{file_uri.replace("/", ":")}")
        else:
            file_uri = URIRef(f"{graph}{file_uri}")

        try:
            file_graph = Graph(identifier=file_uri)

            with open(file_path, "r", encoding="utf-8") as file_handle:
                file_graph.parse(file_handle, publicID=file_graph.identifier)

            for s, p, o in file_graph:
                if isinstance(o, URIRef) and o.startswith(FILE_URI_PREFIX):
                    o_path = o.removeprefix(FILE_URI_PREFIX)
                    o_path = file_path.parent.joinpath(o_path).resolve(strict=True)
                    with open(o_path, "r", encoding="utf-8") as o_file:
                        o_literal = Literal(o_file.read())
                    dataset_graph.add((s, p, o_literal))
                else:
                    dataset_graph.add((s, p, o))

        except Exception:
            print(f"Failed to parse <{file_path.as_uri()}>")
            raise

    return dataset


def execute_queries(root: Path, dataset: Dataset, graph: URIRef) -> None:
    """Helper function to execute all queries on a dataset."""

    target_graph = dataset.get_graph(identifier=graph)

    assert target_graph, f"Missing target graph {graph.n3()}"

    query_files = sorted(iterate_files(root=root, extensions=SPARQL_EXTENSIONS))

    for file_path in query_files:
        print(f"Applying <{file_path.as_uri()}>")

        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                target_graph.update(file_handle.read())

        except Exception:
            print(f"Failed to execute <{file_path.as_uri()}>")
            raise


def generate_void_description(dataset: Dataset, graph: URIRef) -> None:
    """Helper function to generate a VoID dataset description."""

    target_graph = dataset.get_graph(identifier=graph)

    assert target_graph, "Missing graph"

    void_graph, void_uri = generateVoID(
        g=target_graph,
        dataset=graph,
        distinctForPartitions=True,
    )

    assert void_uri == graph, "Mismatched VoID description and graph URI"

    # The following moved all property and class partitions underscore-prefixed
    # URIs to fragments with hash-based identifiers on the dataset URI.

    void_prefix = f"{void_uri}_"
    graph_prefix = f"{graph}#"

    for s, p, o in void_graph:
        if isinstance(s, URIRef) and s.startswith(void_prefix):
            s_hash = (
                sha256(s.encode(encoding="utf-8"), usedforsecurity=False).digest().hex()
            )
            s = URIRef(f"{graph_prefix}{s_hash}")
        if isinstance(o, URIRef) and o.startswith(void_prefix):
            o_hash = (
                sha256(o.encode(encoding="utf-8"), usedforsecurity=False).digest().hex()
            )
            o = URIRef(f"{graph_prefix}{o_hash}")
        target_graph.add((s, p, o))


def serialize_data(
    dataset: Dataset,
    output: Path,
    serialization: SerializationFormat | None,
) -> None:
    """Helper function to serialize data."""

    print(f"Serializing <{output.as_uri()}>")

    if not output.parent.exists():
        output.parent.mkdir()

    if not serialization:
        extension = splitext(output.name)[-1].removeprefix(".")
        for member in SerializationFormat:
            if member.name == extension:
                serialization = member
                break

    assert serialization, "Unable to determine serialization format"

    dataset.serialize(
        destination=output,
        format=serialization.value,
        encoding="utf-8",
    )


@module.command(name="compile")
def compile_data(
    data: Annotated[
        Path,
        Option(
            help="Path to the RDF data to publish",
            parser=path,
        ),
    ],
    graph: Annotated[
        URIRef,
        Option(
            help="The graph URI, also replaces data path in relative URIs",
            parser=uri,
        ),
    ],
    output: Annotated[
        Path,
        Option(
            help="The file path where the data should be serialized",
            parser=path,
        ),
    ],
    queries: Annotated[
        Path | None,
        Option(
            help="Path to SPARQL queries to execute on the data",
            parser=path,
        ),
    ] = None,
    serialization: Annotated[
        SerializationFormat | None,
        Option(help="When omitted, is inferred from output extension"),
    ] = None,
    void: Annotated[
        bool,
        Option(help="Generate a VoID description using RDFLib"),
    ] = False,
) -> None:
    """Compile RDF data from a directory into a single document."""

    dataset = load_data(root=data, graph=graph)

    if queries:
        execute_queries(root=queries, dataset=dataset, graph=graph)

    if void:
        generate_void_description(dataset=dataset, graph=graph)

    serialize_data(dataset=dataset, output=output, serialization=serialization)
