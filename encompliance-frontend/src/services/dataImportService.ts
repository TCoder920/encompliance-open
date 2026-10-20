import api from './api';

/*
  Description: Data import service leveraging backend dry-run/apply endpoints.
*/

export interface DataImportPayload {
  payload: Record<string, unknown>;
  dry_run?: boolean;
}

export interface DataImportResult {
  dry_run: boolean;
  records_created: number;
  warnings?: string[];
}

export const dataImportService = {
  async submitImport(payload: DataImportPayload): Promise<DataImportResult> {
    const response = await api.post<DataImportResult>('/import/data', payload);
    return response.data;
  },
};

export default dataImportService;

