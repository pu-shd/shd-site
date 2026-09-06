# Test and preview container for shd-site.
#
#   docker build -t shd-site .
#   docker run --rm shd-site                  # run the offline checks
#   docker run --rm shd-site pytest -m network  # also resolve outbound links
#   docker run --rm -p 8080:8080 shd-site serve # preview at http://localhost:8080
#
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /site

COPY tests/requirements.txt tests/requirements.txt
RUN pip install --no-cache-dir -r tests/requirements.txt

COPY . .

EXPOSE 8080

ENTRYPOINT ["/site/scripts/entrypoint.sh"]
CMD ["test"]
