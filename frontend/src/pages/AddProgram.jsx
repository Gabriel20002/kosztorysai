import React, { useState } from 'react';

const AddProgram = () => {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        category: 'Software',
        price: ''
    });
    const [status, setStatus] = useState({ type: '', message: '' });
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setStatus({ type: '', message: '' });

        try {
            const response = await fetch('http://localhost:5000/api/programs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                setStatus({ type: 'success', message: 'Program został pomyślnie dodany!' });
                setFormData({ name: '', description: '', category: 'Software', price: '' });
            } else {
                setStatus({ type: 'error', message: data.message || 'Wystąpił błąd podczas dodawania.' });
            }
        } catch (error) {
            console.error('Error adding program:', error);
            setStatus({ type: 'error', message: 'Błąd połączenia z serwerem.' });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="pt-24 pb-16 bg-white min-h-screen">
            <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight mb-4">Dodaj Nowy Program</h1>
                    <p className="text-xl text-slate-600">Wypełnij poniższy formularz, aby dodać program do bazy.</p>
                </div>

                <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-100">
                    {status.message && (
                        <div className={`mb-6 p-4 rounded-lg ${status.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
                            {status.message}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1">Nazwa Programu</label>
                            <input
                                type="text"
                                id="name"
                                name="name"
                                required
                                value={formData.name}
                                onChange={handleChange}
                                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-blue-600 outline-none transition-colors"
                                placeholder="Np. Photoshop"
                            />
                        </div>

                        <div>
                            <label htmlFor="category" className="block text-sm font-medium text-slate-700 mb-1">Kategoria</label>
                            <select
                                id="category"
                                name="category"
                                value={formData.category}
                                onChange={handleChange}
                                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-blue-600 outline-none transition-colors bg-white"
                            >
                                <option value="Software">Software</option>
                                <option value="Hardware">Hardware</option>
                                <option value="Service">Usługa</option>
                                <option value="Other">Inne</option>
                            </select>
                        </div>

                        <div>
                            <label htmlFor="price" className="block text-sm font-medium text-slate-700 mb-1">Cena (PLN)</label>
                            <input
                                type="number"
                                id="price"
                                name="price"
                                value={formData.price}
                                onChange={handleChange}
                                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-blue-600 outline-none transition-colors"
                                placeholder="Np. 199.99"
                                step="0.01"
                            />
                        </div>

                        <div>
                            <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-1">Opis</label>
                            <textarea
                                id="description"
                                name="description"
                                required
                                rows="4"
                                value={formData.description}
                                onChange={handleChange}
                                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-blue-600 outline-none transition-colors resize-none"
                                placeholder="Krótki opis programu..."
                            ></textarea>
                        </div>

                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className={`w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 ${isSubmitting ? 'opacity-75 cursor-not-allowed' : ''}`}
                        >
                            {isSubmitting ? 'Dodawanie...' : 'Dodaj Program'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default AddProgram;
