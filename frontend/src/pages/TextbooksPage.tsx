import { useState } from 'react';
import { Search, BookMarked, Book } from 'lucide-react';
import { mockCourses } from '../data/mockData';
import type { Textbook, ReferenceBook } from '../types';

type AnyBook = Textbook | ReferenceBook;

export default function TextbooksPage() {
  const [tab, setTab] = useState<'textbook' | 'reference'>('textbook');
  const [search, setSearch] = useState('');

  const allTextbooks: Textbook[] = mockCourses.flatMap(c => c.textbooks);
  const allRefs: ReferenceBook[] = mockCourses.flatMap(c => c.referenceBooks);

  const books: AnyBook[] = tab === 'textbook' ? allTextbooks : allRefs;
  const filtered = books.filter(b =>
    b.title.toLowerCase().includes(search.toLowerCase()) ||
    b.author.toLowerCase().includes(search.toLowerCase()) ||
    b.publisher.toLowerCase().includes(search.toLowerCase())
  );

  // Deduplicate by id
  const seen = new Set<string>();
  const unique = filtered.filter(b => {
    if (seen.has(b.id)) return false;
    seen.add(b.id);
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-100 px-6 py-6">
        <h1 className="text-2xl font-bold text-gray-900">Textbooks & References</h1>
        <p className="text-sm text-gray-500 mt-1">Browse all prescribed textbooks and reference materials.</p>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6">
        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="flex border border-gray-200 rounded-xl overflow-hidden bg-white shadow-sm">
            <button
              onClick={() => setTab('textbook')}
              className={`flex items-center gap-2 px-5 py-2.5 text-sm font-medium transition-colors ${
                tab === 'textbook' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <BookMarked size={15} /> Prescribed Textbooks
            </button>
            <button
              onClick={() => setTab('reference')}
              className={`flex items-center gap-2 px-5 py-2.5 text-sm font-medium transition-colors ${
                tab === 'reference' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Book size={15} /> Reference Books
            </button>
          </div>
          <div className="relative flex-1 max-w-sm">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search books..."
              className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
        </div>

        <p className="text-sm text-gray-400 mb-4">{unique.length} book{unique.length !== 1 ? 's' : ''}</p>

        {unique.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-gray-100">
            <BookMarked size={40} className="mx-auto text-gray-300 mb-3" />
            <p className="text-gray-500">No books found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {unique.map((book, i) => {
              const courses = mockCourses.filter(c =>
                book.courseIds.includes(c.id)
              );
              return (
                <div key={book.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex gap-4 hover:shadow-md transition-shadow">
                  <div className={`shrink-0 w-12 h-16 rounded-xl flex items-center justify-center text-white text-xl font-bold
                    ${tab === 'textbook'
                      ? 'bg-gradient-to-b from-blue-500 to-indigo-700'
                      : 'bg-gradient-to-b from-gray-500 to-gray-700'}`}>
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 text-sm leading-snug">{book.title}</h3>
                    <p className="text-sm text-blue-600 mt-1">{book.author}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{book.edition} · {book.publisher}{book.year ? ` · ${book.year}` : ''}</p>
                    {courses.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {courses.map(c => (
                          <span key={c.id} className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full">{c.code}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
