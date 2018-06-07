from googleapiclient.discovery import build

class BigQueryClient(object):
    def __init__(self, http):
        """Creates the BigQuery client connection"""
        self.decorated_http = http
        self.service = build('bigquery', 'v2', self.decorated_http)
# [STOP bqclient-init]

    def getTableData(self, project, dataset, table):
        tablesCollection = self.service.tables()
        request = tablesCollection.get(
            projectId=project,
            datasetId=dataset,
            tableId=table)
        return request.execute(self.decorated_http)
    # [STOP tabledata]

    def getLastModTime(self, project, dataset, table):
        data = self.getTableData(project, dataset, table)
        if data and 'lastModifiedTime' in data:
            return data['lastModifiedTime']
        else:
            return None

    def Query(self, query, project, timeout_in_sec=10):
        query_config = {
            'query': query,
            'timeoutMs': timeout_in_sec*1000
        }
        result_json = (self.service.jobs()
                       .query(projectId=project,
                       body=query_config)
                      .execute(self.decorated_http))
        return result_json
