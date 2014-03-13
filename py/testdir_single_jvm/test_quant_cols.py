import unittest, random, sys, time, re, getpass
sys.path.extend(['.','..','py'])
import h2o, h2o_cmd, h2o_hosts, h2o_browse as h2b, h2o_import as h2i, h2o_glm, h2o_util
import h2o_print as h2p, h2o_gbm

DO_PLOT = getpass.getuser()=='kevin'
DO_MEDIAN = False
MAX_QBINS = 1000
MULTI_PASS = 1

class Basic(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global SEED, localhost
        SEED = h2o.setup_random_seed()
        localhost = h2o.decide_if_localhost()
        if (localhost):
            h2o.build_cloud(1,java_heap_GB=14)
        else:
            h2o_hosts.build_cloud_with_hosts()

    @classmethod
    def tearDownClass(cls):
        # h2o.sleep(3600)
        h2o.tear_down_cloud()

    def test_quant_cols(self):
        h2o.beta_features = True
        SYNDATASETS_DIR = h2o.make_syn_dir()

        tryList = [
            ('/home/kevin/Downloads/t.csv', 15, 11, 'cE', 300), 
            ]

        # h2b.browseTheCloud()
        trial = 0
        xList = []
        eList = []
        fList = []
        
        for (csvPathname, iColCount, oColCount, hex_key, timeoutSecs) in tryList:
            colCount = iColCount + oColCount

            # PARSE*******************************************************
            parseResult = h2i.import_parse(path=csvPathname, schema='put', hex_key=hex_key, timeoutSecs=200, doSummary=False)
            print "Parse result['destination_key']:", parseResult['destination_key']
            inspect = h2o_cmd.runInspect(key=parseResult['destination_key'])
            h2o_cmd.infoFromInspect(inspect, csvPathname)
            numRows = inspect['numRows']
            numCols = inspect['numCols']

            for i in range (1,numCols):
                print "Column", i, "summary"
                h2o_cmd.runSummary(key=hex_key, max_qbins=1, cols=i);

            # print h2o.dump_json(inspect)
            levels = h2o.nodes[0].levels(source=hex_key)
            print "levels result:", h2o.dump_json(levels)

            (missingValuesDict, constantValuesDict, enumSizeDict, colTypeDict, colNameDict) = \
                h2o_cmd.columnInfoFromInspect(parseResult['destination_key'], exceptionOnMissingValues=False)

            # error if any col has constant values
            if len(constantValuesDict) != 0:
                # raise Exception("Probably got a col NA'ed and constant values as a result %s" % constantValuesDict)
                print "Probably got a col NA'ed and constant values as a result %s" % constantValuesDict
            
            # start after the last input col
            for column in range(iColCount, iColCount+oColCount):

                # QUANTILE*******************************************************
                
                quantile = 0.5 if DO_MEDIAN else .999
                # first output col. always fed by an exec cut, so 0?
                start = time.time()
                # file has headers. use col index
                q = h2o.nodes[0].quantiles(source_key=hex_key, column=column,
                    quantile=quantile, max_qbins=MAX_QBINS, multiple_pass=1)
                h2p.red_print("result:", q['result'], "quantile", quantile, 
                    "interpolated:", q['interpolated'], "iterations", q['iterations'])
                elapsed = time.time() - start
                print "quantile end on ", hex_key, 'took', elapsed, 'seconds.'
                quantileTime = elapsed

                # remove all keys*******************************************************
                # what about hex_key?
                if 1==0:
                    start = time.time()
                    h2o.nodes[0].remove_all_keys()
                    elapsed = time.time() - start
                    print "remove all keys end on ", csvFilename, 'took', elapsed, 'seconds.'

                trial += 1
                execTime = 0
                xList.append(column)
                eList.append(execTime)
                fList.append(quantileTime)



        #****************************************************************
        # PLOTS. look for eplot.jpg and fplot.jpg in local dir?
        if DO_PLOT:
            xLabel = 'column (0 is first)'
            eLabel = 'exec cut time'
            fLabel = 'quantile time'
            eListTitle = ""
            fListTitle = ""
            h2o_gbm.plotLists(xList, xLabel, eListTitle, eList, eLabel, fListTitle, fList, fLabel, server=True)



if __name__ == '__main__':
    h2o.unit_main()
