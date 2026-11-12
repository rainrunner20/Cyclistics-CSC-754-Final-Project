# Understanding the NYC Open Data client

This walkthrough explains the *why* behind the code. The comments inside the Python
files are intentionally short, like comments in a normal engineering repository.

## 1. Configuration (`DATASETS`)

The dataset mapping is an **allowlist**: only known IDs can be queried. If the
Socrata portal changes, we have one place to update the IDs or required fields.

## 2. `build_url(dataset, limit)`

Builds an HTTPS address. It checks dataset names and limits, and it uses
`urlencode` rather than manually building query strings. Try calling it with
`limit=0` and explain why it raises `ValueError`.

## 3. `validate_records(dataset, rows)`

Checks that the API returned a list of objects with the expected keys. For
count rows, a nonnegative finite number is required. The raw string is kept
because this milestone is ingestion, not a complete cleaning/transformation step.

## 4. `fetch_sample(dataset, limit, token)`

Performs the HTTP request with a timeout and retries only temporary failures.
An optional app token goes in an HTTP header rather than in logged URLs. The
saved response includes provenance: where and when it was downloaded.

## 5. `main()`

Exposes the module from the command line, checks arguments, and writes JSON to
an output path. This is the entry point invoked from Docker.

## 6. The tests

`unittest.mock.patch` replaces the real HTTP request with a fake response. We
can test validation and error handling even when NYC Open Data is unreachable.
A **unit test passing** does not mean a **live API integration** was verified.

## Try a safe experiment yourself

1. Run the existing test suite and write down the result.
2. Change a test input from `counts="3"` to `counts="-3"` and predict the result.
3. Run the test to see whether the behavior matches your prediction.
4. Restore the test, then add a new test case for `limit=True` (should be rejected).
5. Note the reason for this behavior in your development journal.

## Questions you should be able to answer

- Why do we cap the result size?
- Why are HTTP 429 and 503 retried, but HTTP 400 is not?
- What does an API token do, and why don't we write it to JSON?
- Why isn't a five-row sample enough to estimate a cyclist arrival rate?
- How would you change the code if a dataset's API schema changed?

## CSC 754 connection

This is data preparation for model inputs. Actual validation of the simulation
comes later, when we compare its behavior with appropriate observations. A
successful HTTP request is **not** evidence that a simulation is accurate.
