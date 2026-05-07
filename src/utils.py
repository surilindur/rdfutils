"""Common utilities and types for the application."""

from enum import StrEnum
from typing import Mapping
from typing import Iterable
from pathlib import Path

from rdflib.term import URIRef


class SerializationFormat(StrEnum):
    """
    Default file extensions and format keywords for RDFLib serialization.

    https://rdflib.readthedocs.io/en/7.1.1/intro_to_parsing.html
    """

    ttl = "turtle"  # pylint: disable=invalid-name
    nt = "nt"  # pylint: disable=invalid-name
    rdf = "pretty-xml"  # pylint: disable=invalid-name
    n3 = "n3"  # pylint: disable=invalid-name
    jsonld = "json-ld"  # pylint: disable=invalid-name
    trig = "trig"  # pylint: disable=invalid-name
    trix = "trix"  # pylint: disable=invalid-name
    nq = "nquads"  # pylint: disable=invalid-name


SERIALIZATION_CONTENT_TYPES: Mapping[SerializationFormat, str] = {
    SerializationFormat.ttl: "text/turtle",
    SerializationFormat.jsonld: "application/ld+json",
    SerializationFormat.n3: "text/n3",
    SerializationFormat.nq: "application/n-quads",
    SerializationFormat.nt: "application/n-triples",
    SerializationFormat.rdf: "application/rdf+xml",
    SerializationFormat.trig: "application/trig",
    SerializationFormat.trix: "application/trix",
}

SPARQL_EXTENSIONS = (".rq", ".sparql")

RDF_EXTENSIONS = tuple(f".{k.name}" for k in SerializationFormat)

FILE_URI_PREFIX = "file://"


def uri(value: str) -> URIRef:
    """Helper function to parse URIs."""
    return URIRef(value)


def path(value: str) -> Path:
    """Helper function to resolve absolute paths."""
    return Path(value).resolve()


def iterate_files(root: Path, extensions: tuple[str, ...]) -> Iterable[Path]:
    """Helper function to iterate over all files with specific extension."""

    queue = [root]

    while queue:
        current_path = queue.pop(0)

        if current_path.is_dir():
            queue.extend(current_path.iterdir())

        elif current_path.name.endswith(extensions):
            yield current_path
