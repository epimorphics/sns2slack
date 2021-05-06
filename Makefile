NAME=sns2slack
PYTHON_VERSION=3.8
VERSION?=SNAPSHOT
REPO?=293385631482.dkr.ecr.eu-west-1.amazonaws.com/epimorphics/${NAME}
LIBS=libs
ZIP=layer-${VERSION}.zip

all: zip image

image:
	@docker build -t ${REPO}:${VERSION} .

publish:
	@docker push ${REPO}:${VERSION}

zip: ${ZIP}

${ZIP}: requirements.txt
	@/usr/bin/python${PYTHON_VERSION} -m pip install -t ${LIBS} -r requirements.txt --upgrade
	@cd ${LIBS}; zip -r ../${ZIP} .

release: zip
	@aws s3 cp ${ZIP} s3://epi-repository/release/lambda-layer/${NAME}/python-${PYTHON_VERSION}/${ZIP}

clean:
	@rm -rf ${LIBS} ${ZIP}

.PHONY:	clean image publish release zip 
