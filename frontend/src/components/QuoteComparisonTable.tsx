import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Clock, Package, Star } from 'lucide-react';

interface Quote {
    quote_id: number;
    supplier_name: string;
    unit_price: number;
    total_price: number;
    delivery_days: number;
    stock_available: number | null;
    notes: string;
    price_color: 'green' | 'yellow' | 'red';
    delivery_color: 'green' | 'yellow' | 'red';
    reliability_score: number;
}

interface QuoteComparisonTableProps {
    taskId: number;
}

const QuoteComparisonTable: React.FC<QuoteComparisonTableProps> = ({ taskId }) => {
    const [quotes, setQuotes] = useState<Quote[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedQuote, setSelectedQuote] = useState<number | null>(null);

    useEffect(() => {
        fetchQuotes();
    }, [taskId]);

    const fetchQuotes = async () => {
        try {
            const response = await fetch(`http://localhost:8000/api/v1/quotes/task/${taskId}/comparison`);
            const data = await response.json();
            setQuotes(data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching quotes:', error);
            setLoading(false);
        }
    };

    const getColorClass = (color: string) => {
        switch (color) {
            case 'green': return 'bg-green-500/20 text-green-400 border-green-500/50';
            case 'yellow': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
            case 'red': return 'bg-red-500/20 text-red-400 border-red-500/50';
            default: return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">Quote Comparison</h2>
                <div className="flex items-center space-x-2 text-sm">
                    <div className="flex items-center space-x-1">
                        <div className="w-3 h-3 rounded-full bg-green-500" />
                        <span className="text-gray-300">Best Value</span>
                    </div>
                    <div className="flex items-center space-x-1">
                        <div className="w-3 h-3 rounded-full bg-yellow-500" />
                        <span className="text-gray-300">Competitive</span>
                    </div>
                    <div className="flex items-center space-x-1">
                        <div className="w-3 h-3 rounded-full bg-red-500" />
                        <span className="text-gray-300">Premium</span>
                    </div>
                </div>
            </div>

            <div className="grid gap-4">
                {quotes.map((quote) => (
                    <div
                        key={quote.quote_id}
                        className={`bg-white/5 backdrop-blur-lg rounded-xl border-2 transition-all cursor-pointer ${selectedQuote === quote.quote_id
                                ? 'border-purple-500 shadow-lg shadow-purple-500/50'
                                : 'border-white/10 hover:border-white/30'
                            }`}
                        onClick={() => setSelectedQuote(quote.quote_id)}
                    >
                        <div className="p-6">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h3 className="text-xl font-bold text-white mb-1">{quote.supplier_name}</h3>
                                    <div className="flex items-center space-x-2">
                                        <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                                        <span className="text-sm text-gray-300">{quote.reliability_score}/100 Reliability</span>
                                    </div>
                                </div>
                                {selectedQuote === quote.quote_id && (
                                    <span className="px-3 py-1 bg-purple-500 text-white text-sm font-semibold rounded-full">
                                        Selected
                                    </span>
                                )}
                            </div>

                            <div className="grid grid-cols-4 gap-4 mb-4">
                                {/* Price */}
                                <div className={`rounded-lg p-4 border-2 ${getColorClass(quote.price_color)}`}>
                                    <div className="flex items-center space-x-2 mb-2">
                                        {quote.price_color === 'green' ? (
                                            <TrendingDown className="w-5 h5 text-green-400" />
                                        ) : (
                                            <TrendingUp className="w-5 h-5 text-red-400" />
                                        )}
                                        <span className="text-sm font-semibold">Price</span>
                                    </div>
                                    <p className="text-2xl font-bold">${quote.unit_price.toFixed(2)}</p>
                                    <p className="text-xs opacity-70">per unit</p>
                                    <p className="text-sm mt-1">${quote.total_price.toFixed(2)} total</p>
                                </div>

                                {/* Delivery */}
                                <div className={`rounded-lg p-4 border-2 ${getColorClass(quote.delivery_color)}`}>
                                    <div className="flex items-center space-x-2 mb-2">
                                        <Clock className="w-5 h-5" />
                                        <span className="text-sm font-semibold">Delivery</span>
                                    </div>
                                    <p className="text-2xl font-bold">{quote.delivery_days}</p>
                                    <p className="text-xs opacity-70">days</p>
                                </div>

                                {/* Stock */}
                                <div className="rounded-lg p-4 border-2 bg-blue-500/20 text-blue-400 border-blue-500/50">
                                    <div className="flex items-center space-x-2 mb-2">
                                        <Package className="w-5 h-5" />
                                        <span className="text-sm font-semibold">Stock</span>
                                    </div>
                                    <p className="text-2xl font-bold">{quote.stock_available || 'N/A'}</p>
                                    <p className="text-xs opacity-70">available</p>
                                </div>

                                {/* Score */}
                                <div className="rounded-lg p-4 border-2 bg-purple-500/20 text-purple-400 border-purple-500/50">
                                    <div className="flex items-center space-x-2 mb-2">
                                        <Star className="w-5 h-5" />
                                        <span className="text-sm font-semibold">Overall</span>
                                    </div>
                                    <p className="text-2xl font-bold">
                                        {Math.round((100 - quote.unit_price * 10 + quote.reliability_score) / 2)}
                                    </p>
                                    <p className="text-xs opacity-70">score</p>
                                </div>
                            </div>

                            {quote.notes && (
                                <div className="bg-black/20 rounded-lg p-3">
                                    <p className="text-sm text-gray-300">
                                        <span className="font-semibold text-white">Notes: </span>
                                        {quote.notes}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {quotes.length === 0 && (
                <div className="text-center py-12">
                    <p className="text-gray-400">No quotes available yet. Waiting for supplier responses...</p>
                </div>
            )}
        </div>
    );
};

export default QuoteComparisonTable;
