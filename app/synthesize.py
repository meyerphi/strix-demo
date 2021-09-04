import sys
import os
import logging
import html
import subprocess

DOT_PATH="./dot"
STRIX_PATH="./strix"
ABC_PATH="./abc"
AUTFILT_PATH="./autfilt"

ORIGIN="https://meyerphi.github.io"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def bad_request(message):
    message = html.escape(message).replace("\n", "<br>")
    return {
        "statusCode": 400,
        "body": message,
        "headers": {
            'Content-Type': 'text/html; charset=utf-8',
            'Access-Control-Allow-Origin': ORIGIN
        }
    }

def image_response(body):
    return {
        "statusCode": 200,
        "body": body,
        "headers": {
            'Content-Type': 'image/svg+xml; charset=utf-8',
            'Access-Control-Allow-Origin': ORIGIN
        }
    }

def handler(event, context):
    query = event.get('queryStringParameters')
    if query is None:
        return bad_request("no query string parameters")
    formula = query.get('formula')
    inputs = query.get('inputs')
    outputs = query.get('outputs')
    minimize = query.get('minimize')
    labels = query.get('labels')
    format = query.get('format')
    if formula is None:
        return bad_request("formula missing")
    if inputs is None:
        return bad_request("inputs missing")
    if outputs is None:
        return bad_request("outputs missing")
    if minimize is None:
        return bad_request("minimize missing")
    if labels is None:
        return bad_request("labels missing")
    if format is None:
        return bad_request("format missing")
    if minimize != '0' and minimize != '1':
        return bad_request("minimize must be '0' or '1'")
    minimize = (minimize == '1')
    if labels != '0' and labels != '1':
        return bad_request("labels must be '0' or '1'")
    labels = (labels == '1')
    if format != "mealy" and format != "bdd" and format != "aiger":
        return bad_request("format must be 'mealy', 'bdd' or 'aiger'")

    logger.info("formula: {}".format(formula))
    logger.info("inputs: {}".format(inputs))
    logger.info("outputs: {}".format(outputs))
    logger.info("minimize: {}".format(minimize))
    logger.info("labels: {}".format(labels))
    logger.info("format: {}".format(format))

    controller_path = '/tmp/controller'
    dot_path = '/tmp/controller.dot'
    strix_args = [STRIX_PATH, '--formula', formula, '--ins', inputs, '--outs', outputs, '-O', controller_path]
    if format == 'mealy':
        strix_args.extend(['-o', 'hoa'])
        if minimize:
            strix_args.extend(['-m', 'both'])
        else:
            strix_args.extend(['-m', 'none'])
    elif format == 'aiger':
        strix_args.extend(['-o', 'aig'])
        if minimize:
            strix_args.extend(['--aiger'])
        else:
            strix_args.extend(['-m', 'none', '--reordering', 'none', '--compression', 'none'])
    elif format == 'bdd':
        strix_args.extend(['-o', 'bdd'])
        if minimize:
            strix_args.extend(['-m', 'both', '--reordering', 'mixed'])
        else:
            strix_args.extend(['-m', 'none', '--reordering', 'none', '--compression', 'none'])
    if labels:
        strix_args.extend(['--label', 'structured'])

    try:
        result = subprocess.run(strix_args, capture_output=True)
    except Exception as e:
        return bad_request("Error: strix subprocess raised an exception: {}".format(e))
    if result.returncode != 0:
        return bad_request("Error: strix exited with return code {}\n{}\n{}".format(result.returncode, result.stdout, result.stderr))
    if not result.stdout:
        return bad_request("Error: strix produced no output\n{}".format(result.stderr))

    realizability_result = result.stdout.decode('utf-8').strip()
    if realizability_result != 'REALIZABLE' and realizability_result != 'UNREALIZABLE':
        return bad_request("Error: strix returned invalid result: {}".format(realizability_result));

    if format == 'mealy':
        try:
            result = subprocess.run([AUTFILT_PATH, '--merge-transitions', '--dot=A', '-F', controller_path, '-o', dot_path], capture_output=True)
        except Exception as e:
            return bad_request("Error: autfilt subprocess raised an exception: {}".format(e))
        if result.returncode != 0:
            return bad_request("Error: autfilt exited with return code {}\n{}\n{}".format(result.returncode, result.stdout, result.stderr))
    elif format == 'aiger':
        try:
            result = subprocess.run([ABC_PATH, '-c', "read_aiger {}; write_dot {}".format(controller_path, dot_path)], capture_output=True)
        except Exception as e:
            return bad_request("Error: abc subprocess raised an exception: {}".format(e))
        if result.returncode != 0:
            return bad_request("Error: abc exited with return code {}\n{}\n{}".format(result.returncode, result.stdout, result.stderr))
    elif format == 'bdd':
        dot_path = controller_path

    # add result as title
    clean_dot_path = '/tmp/controller_clean.dot'
    with open(dot_path, 'r') as dot_file:
        with open(clean_dot_path, 'w') as clean_dot_file:
            for line in dot_file.readlines():
                clean_dot_file.write(line)
                clean_dot_file.write("\n")
                if line.startswith('digraph'):
                    clean_dot_file.write('labelloc="t";\n');
                    clean_dot_file.write('label="{}"\n'.format(realizability_result));

    try:
        result = subprocess.run([DOT_PATH, "-Tsvg", clean_dot_path], capture_output=True)
    except Exception as e:
        return bad_request("Error: dot subprocess raised an exception: {}".format(e))
    if result.returncode != 0:
        return bad_request("Error: dot exited with return code {}\n{}\n{}".format(result.returncode, result.stdout, result.stderr))
    if not result.stdout:
        return bad_request("Error: dot produced no output\n{}".format(result.stderr))
    image_bytes = result.stdout

    return image_response(image_bytes)
