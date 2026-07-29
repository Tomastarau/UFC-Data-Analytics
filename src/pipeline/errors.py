class PipelineError(Exception):
    """Base class for ingestion failures that must abort a run."""


class ChallengeError(PipelineError):
    """The server returned an anti-bot challenge page instead of content."""


class ContractError(PipelineError):
    """A page parsed without error but violates an expected structural invariant."""
