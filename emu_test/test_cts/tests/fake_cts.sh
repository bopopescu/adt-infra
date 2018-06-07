#!/bin/bash

# output the expected result line, wait for exit.

EXEC_FILE=$0
RUN=$1
CTS=$2
PLAN_KEYWORD=$3
SUBPLAN=$4

EXEC_DIR=$(dirname "${EXEC_FILE}")

# In a real run, the date/time of the run would be used instead of ${SUBPLAN}.
mkdir /tmp/fake_cts_output/${SUBPLAN}

# Copy the reference output as the output of this run. (A parseable XML file,
# with accompanying css and xsl files.)
cp ${EXEC_DIR}/ref-testResult.xml /tmp/fake_cts_output/${SUBPLAN}/testResult.xml
cp ${EXEC_DIR}/../cts_result.css /tmp/fake_cts_output/${SUBPLAN}
cp ${EXEC_DIR}/../cts_result.xsl /tmp/fake_cts_output/${SUBPLAN}

echo "Created /tmp/fake_cts_output/${SUBPLAN}, wrote testResult.xml there."

echo "XML test result file generated at ${SUBPLAN}. Passed 123, Failed 88, Not Executed 16\n"

while true; do
  read INPUT
  if [ "${INPUT}" = "exit" ]; then
    echo "Received exit command"
    break;
  fi
done
