/*
  Description: Note service for handling note operations on the frontend.
  Purpose: Provides methods for interacting with the notes API endpoints.
*/
import axios from 'axios';

// Define the base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const NOTES_API_URL = `${API_BASE_URL}/api/notes/`;

// Define types
export interface Note {
  id: number;
  title: string;
  content: string | null;
  is_pinned: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  user_id: number;
}

export interface NoteCreate {
  title: string;
  content?: string | null;
  is_pinned?: boolean;
  is_archived?: boolean;
}

export interface NoteUpdate {
  title?: string;
  content?: string | null;
  is_pinned?: boolean;
  is_archived?: boolean;
}

export interface NoteListResponse {
  notes: Note[];
  total: number;
}

export interface NotesFilter {
  skip?: number;
  limit?: number;
  search?: string;
  sort_by?: 'created_at' | 'updated_at' | 'title';
  sort_order?: 'asc' | 'desc';
  show_archived?: boolean;
}

export interface BulkOperationResponse {
  count: number;
  message: string;
}

// Note service class
export class NoteService {
  private static instance: NoteService;
  private token: string | null = null;

  private constructor() {
    // Get token from local storage
    this.token = localStorage.getItem('token');
  }

  // Singleton pattern
  public static getInstance(): NoteService {
    if (!NoteService.instance) {
      NoteService.instance = new NoteService();
    }
    return NoteService.instance;
  }

  // Update token (e.g., after login)
  public updateToken(token: string): void {
    this.token = token;
  }

  // Get authorization header
  private getAuthHeader() {
    return {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    };
  }

  // Create a new note
  public async createNote(note: NoteCreate): Promise<Note> {
    const response = await axios.post<Note>(
      NOTES_API_URL,
      note,
      this.getAuthHeader()
    );
    return response.data;
  }

  // Get all notes with filtering, sorting, and pagination
  public async getNotes(filters: NotesFilter = {}): Promise<NoteListResponse> {
    const {
      skip = 0,
      limit = 100,
      search,
      sort_by = 'updated_at',
      sort_order = 'desc',
      show_archived = false,
    } = filters;

    let url = `${NOTES_API_URL}?skip=${skip}&limit=${limit}&sort_by=${sort_by}&sort_order=${sort_order}&show_archived=${show_archived}`;
    
    if (search) {
      url += `&search=${encodeURIComponent(search)}`;
    }

    const response = await axios.get<NoteListResponse>(url, this.getAuthHeader());
    return response.data;
  }

  // Get a specific note by ID
  public async getNote(id: number): Promise<Note> {
    const response = await axios.get<Note>(
      `${NOTES_API_URL}/${id}`,
      this.getAuthHeader()
    );
    return response.data;
  }

  // Update a note
  public async updateNote(id: number, note: NoteUpdate): Promise<Note> {
    const response = await axios.put<Note>(
      `${NOTES_API_URL}/${id}`,
      note,
      this.getAuthHeader()
    );
    return response.data;
  }

  // Delete a note
  public async deleteNote(id: number): Promise<void> {
    await axios.delete(`${NOTES_API_URL}/${id}`, this.getAuthHeader());
  }

  // Archive a note
  public async archiveNote(id: number): Promise<Note> {
    const response = await axios.post<Note>(
      `${NOTES_API_URL}/${id}/archive`,
      {},
      this.getAuthHeader()
    );
    return response.data;
  }

  // Unarchive a note
  public async unarchiveNote(id: number): Promise<Note> {
    const response = await axios.post<Note>(
      `${NOTES_API_URL}/${id}/unarchive`,
      {},
      this.getAuthHeader()
    );
    return response.data;
  }

  // Pin a note
  public async pinNote(id: number): Promise<Note> {
    const response = await axios.post<Note>(
      `${NOTES_API_URL}/${id}/pin`,
      {},
      this.getAuthHeader()
    );
    return response.data;
  }

  // Unpin a note
  public async unpinNote(id: number): Promise<Note> {
    const response = await axios.post<Note>(
      `${NOTES_API_URL}/${id}/unpin`,
      {},
      this.getAuthHeader()
    );
    return response.data;
  }

  // Delete all notes
  public async deleteAllNotes(archivedOnly: boolean = false): Promise<BulkOperationResponse> {
    const response = await axios.delete<BulkOperationResponse>(
      `${NOTES_API_URL}bulk/delete-all?archived_only=${archivedOnly}`,
      this.getAuthHeader()
    );
    return response.data;
  }

  // Archive all notes
  public async archiveAllNotes(): Promise<BulkOperationResponse> {
    const response = await axios.post<BulkOperationResponse>(
      `${NOTES_API_URL}bulk/archive-all`,
      {},
      this.getAuthHeader()
    );
    return response.data;
  }
}

// Export a singleton instance
export const noteService = NoteService.getInstance(); 