import h2o, h2o_cmd, h2o_jobs
import time, re, getpass

import os

# hdfs/maprfs/s3/s3n paths should be absolute from the bucket (top level)
# so only walk around for local
def find_local_bucket(bucket, pathWithRegex):
    if bucket is None:  # good for absolute path name
        bucketPath = ""

    if bucket = ".":
        bucketPath = os.getcwd()

    # does it work to use bucket "." to get current directory
    elif os.environ['H2O_BUCKETS_ROOT']:
        root = os.environ(['H2O_BUCKETS_ROOT']
        print "Using H2O_BUCKETS_ROOT environment variable:", root

        rootPath = os.path.abspath(root)
        if not (os.path.exists(rootPath)
            raise Exception("buckets root %s doesn't exist." % rootPath

        bucketPath = os.path.join(bucketsRoot, bucket)
        if not (os.path.exists(bucketPath)
            raise Exception("bucket path %s doesn't exist." % bucketPath

    else:
        (head, tail) = os.path.split(os.path.abspath(bucket))
        verboseprint("find_bucket looking upwards from", head, "for", tail)
        # don't spin forever 
        levels = 0
        while not (os.path.exists(os.path.join(head, tail))):
            print "Didn't find", tail, "at", head
            head = os.path.split(head)[0]
            levels += 1
            if (levels==10):
                raise Exception("unable to find bucket: %s" % bucket)

        rootPath = head
        bucketPath = os.path.join(head, tail)

    if pathWithRegex is None:
        localPath = bucketPath
        return (localPath, None)

    # if there is a "/" in the path, that means it's not just a pattern
    # split it
    # otherwise it is a pattern. use it to search for files in python first? 
    # FIX! do that later
    elif "/" in pathWithRegex:
        (head, tail) = os.path.split(pathWithRegex)
        localPath = os.path.join(bucketPath, head)
        if not (os.path.exists(localPath):
            raise Exception("%s doesn't exist. %s under %s may be wrong?" % (localPath, head, bucketPath))
        return (localPath, tail)
    
    else:
        localPath = bucketPath
        return (localPath, pathWithRegex)


# passes additional params thru kwargs for parse
# use_header_file
# header
# exclude
# src_key can be a pattern
# can import with path= a folder or just one file
def import_only(node=None, path=None, schema="put", bucket="datasets"
    timeoutSecs=30, retryDelaySecs=0.5, initialDelaySecs=0.5, pollTimeoutSecs=180, noise=None,
    noPoll=False, doSummary=True, **kwargs):

    # no bucket is sometimes legal (fixed path)
    if not node: node = h2o.nodes[0]

    if not bucket:
        bucket = "home-0xdiag-datasets"

    if schema=='put':
        if not path: raise Exception('path=, No file to putfile')
        (localPath, filename) = find_bucket(bucket, path)
        localFile = os.join(localPath. filename)
        key = node.put_file(localFile, key=src_key, timeoutSecs=timeoutSecs)
        return key

    elif schema=='s3' or node.redirect_import_folder_to_s3_path:
        importResult = node.import_s3(bucket, timeoutSecs=timeoutSecs)

    elif schema=='s3n':
        hdfsPrefix = schema + ":/"
        URI = hdfsPrefix + path
        importResult = node.import_hdfs(URI, timeoutSecs=timeoutSecs)

    elif schema=='maprfs':
        hdfsPrefix = schema + "://"
        URI = hdfsPrefix + path
        importResult = node.import_hdfs(URI, timeoutSecs=timeoutSecs)

    elif schema=='hdfs' or node.redirect_import_folder_to_s3n_path:
        hdfsPrefix = schema + "://" + node.hdfs_name_node
        URI = hdfsPrefix + path
        importResult = node.import_hdfs(URI, timeoutSecs=timeoutSecs)

    elif schema=='local':
        (localPath, filename) = find_bucket(bucket, path)
        importFolderResult = node.import_files(localPath, timeoutSecs=timeoutSecs)

    return importFolderResult

# can take header, header_from_file, exclude params
def parse(node=None, pattern=None, hex_key=None, ,
    timeoutSecs=30, retryDelaySecs=0.5, initialDelaySecs=0.5, pollTimeoutSecs=180, noise=None,
    noPoll=False, **kwargs):
    if hex_key is None:
        # don't rely on h2o default key name
        key2 = key + '.hex'
    else:
        key2 = hex_key

    parseResult = parse(node, pattern, hex_key, ,
        timeoutSecs, retryDelaySecs, initialDelaySecs, pollTimeoutSecs, noise,
        noPoll, **kwargs):

    parseResult['python_source'] = pattern
    return parseResult


def import(node=None, path=None, src_key=None, hex_key=None, schema="put", bucket="datasets"
    timeoutSecs=30, retryDelaySecs=0.5, initialDelaySecs=0.5, pollTimeoutSecs=180, noise=None,
    noPoll=False, doSummary=False, **kwargs):

    importResult = import_only(node, path, schema, bucket,
        timeoutSecs, retryDelaySecs, initialDelaySecs, pollTimeoutSecs, noise
        noPoll, **kwargs):

    parseResult = parse(node, pattern, hex_key, schema,
        timeoutSecs, retryDelaySecs, initialDelaySecs, pollTimeoutSecs, noise,
        noPoll, **kwargs):

    # do SummaryPage here too, just to get some coverage
    if doSummary:
        node.summary_page(myKey2, timeoutSecs=timeoutSecs)
    return parseResult
