/*
  Description: PDF service for managing PDF upload, listing, download, and deletion via the document service API.
  Purpose: Provides a simplified interface for handling PDF documents in compliance workflows.
*/
import documentService, { Document } from './documentService';

// Alias Document as PDF for backward compatibility
export type PDF = Document;

export interface PDFListResponse {
  pdfs: PDF[];
}

class PDFService {
  async uploadPDF(file: File, customLabel?: string): Promise<PDF> {
    try {
      const result = await documentService.uploadDocument(file, customLabel);
      return result;
    } catch (err) {
      throw err;
    }
  }

  async listPDFs(): Promise<PDF[]> {
    try {
      const documents = await documentService.listDocuments();
      return documents;
    } catch (err) {
      return [];
    }
  }

  async downloadPDF(pdfId: number): Promise<string> {
    try {
      return await documentService.downloadDocument(pdfId.toString());
    } catch (err) {
      throw err;
    }
  }

  async deletePDF(pdfId: number): Promise<PDF> {
    try {
      return await documentService.deleteDocument(pdfId);
    } catch (err) {
      throw err;
    }
  }
}

export default new PDFService(); 