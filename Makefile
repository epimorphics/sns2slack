NAME?=sns2slack
PYTHON_VERSION=3.10
VERSION?=SNAPSHOT
REPO?=293385631482.dkr.ecr.eu-west-1.amazonaws.com/epimorphics/${NAME}
LIBS=libs
LAYER=layer-${VERSION}.zip
LAMBDA=${NAME}-${VERSION}.zip
SCRIPT=${NAME}.py

all: lambda layer image

image:
	@docker build --build-arg PYTHON_VERSION=${PYTHON_VERSION} -t ${REPO}:${VERSION} .

publish:
	@docker push ${REPO}:${VERSION}

lambda: ${LAMBDA}

layer: ${$LAYER}

${LAMBDA}: ${SCRIPT} ${LIBS}
	@zip -r ${LAMBDA} ${SCRIPT} ./${LIBS}

${LAYER}: ${LIBS}
	@cd ${LIBS}; zip -r ../${LAYER} .

${LIBS}: requirements.txt
	@/usr/bin/pip3 install -t ${LIBS} -r requirements.txt --upgrade

release: ${LAMBDA}
	@aws s3 cp ${LAMBDA} s3://epi-repository/release/lambda/${NAME}/python${PYTHON_VERSION}/${LAMBDA}

upload: ${LAYER}
	@aws s3 cp ${$LAYER} s3://epi-repository/release/lambda-layer/${NAME}/python${PYTHON_VERSION}/${$LAYER}

clean:
	@rm -rf ${LIBS} *.zip

.PHONY:	clean image publish release upload
