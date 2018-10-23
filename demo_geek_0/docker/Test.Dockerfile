FROM gmirror/geek-digest-base:latest

WORKDIR /app
COPY . .

CMD PROJECT_ENV=test nosetests -v --with-xunit --xunit-file=nosetests.xml --cover-package=geek_digest --with-xcoverage
