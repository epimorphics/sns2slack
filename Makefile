VERSION?=SNAPSHOT
REPO?=293385631482.dkr.ecr.eu-west-1.amazonaws.com/epimorphics/sns2slack

all: image

image:
	@docker build -t ${REPO}:${VERSION} .

publish:
	@docker push ${REPO}:${VERSION}
