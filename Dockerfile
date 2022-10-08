ARG MINICONDA_IMAGE_TAG=4.10.3-alpine

FROM continuumio/miniconda3:$MINICONDA_IMAGE_TAG AS base

# add bash, because it's not available by default on alpine
RUN apk add --no-cache bash

WORKDIR /app/

# install poetry
COPY ./requirements.txt ./requirements.txt
RUN python3 -m pip install --no-cache-dir -r ./requirements.txt

# create new environment
# see: https://jcristharif.com/conda-docker-tips.html
# warning: for some reason conda can hang on "Executing transaction" for a couple of minutes
COPY environment.yaml ./environment.yaml
RUN conda env create -f ./environment.yaml && \
    conda clean -afy && \
    find /opt/conda/ -follow -type f -name '*.a' -delete && \
    find /opt/conda/ -follow -type f -name '*.pyc' -delete && \
    find /opt/conda/ -follow -type f -name '*.js.map' -delete

# "activate" environment for all commands (note: ENTRYPOINT is separate from SHELL)
SHELL ["conda", "run", "--no-capture-output", "-n", "cilroy", "/bin/bash", "-c"]

WORKDIR /app/cilroy/

# add poetry files
COPY ./cilroy/pyproject.toml ./cilroy/poetry.lock ./

FROM base AS test

# install dependencies only (notice that no source code is present yet) and delete cache
RUN poetry install --no-root --only main,test && \
    rm -rf ~/.cache/pypoetry

# add source, tests and necessary files
COPY ./cilroy/src/ ./src/
COPY ./cilroy/tests/ ./tests/
COPY ./cilroy/LICENSE ./cilroy/README.md ./

# build wheel by poetry and install by pip (to force non-editable mode)
RUN poetry build -f wheel && \
    python -m pip install --no-deps --no-index --no-cache-dir --find-links=dist cilroy

# add entrypoint
COPY ./entrypoint.sh ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh", "pytest"]
CMD []

FROM base AS production

# install dependencies only (notice that no source code is present yet) and delete cache
RUN poetry install --no-root --only main && \
    rm -rf ~/.cache/pypoetry

# add source and necessary files
COPY ./cilroy/src/ ./src/
COPY ./cilroy/LICENSE ./cilroy/README.md ./

# build wheel by poetry and install by pip (to force non-editable mode)
RUN poetry build -f wheel && \
    python -m pip install --no-deps --no-index --no-cache-dir --find-links=dist cilroy

# add entrypoint
COPY ./entrypoint.sh ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh", "cilroy"]
CMD []
