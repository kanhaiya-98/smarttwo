import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { DollarSign, Clock, Trophy } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Quote {
    quote_id: number;
    supplier_name: string;
    supplier_code: string;
    unit_price: number;
    delivery_days: number;
    quantity_available: number;
    reliability_score: number;
    is_fast_delivery: boolean;
    response_time: number;
    valid_until: string;
}

interface QuoteComparisonProps {
    taskId: number | null;
}

export function QuoteComparison({ taskId }: QuoteComparisonProps) {
    const [quotes, setQuotes] = useState<Quote[]>([]);
    // const [loading, setLoading] = useState(false); // Removed as per instruction

    useEffect(() => {
        if (!taskId) return;

        const fetchQuotes = async () => {
            // setLoading(true); // Removed as per instruction
            try {
                const response = await axios.get(`${API_URL}/api/v1/negotiation/task/${taskId}/quotes`);
                setQuotes(response.data);
            } catch (error) {
                console.error("Error fetching quotes:", error);
            } finally {
                // setLoading(false); // Removed as per instruction
            }
        };

        // Poll for quotes while logic runs
        fetchQuotes();
        const interval = setInterval(fetchQuotes, 2000);
        return () => clearInterval(interval);

    }, [taskId]);

    if (!taskId || quotes.length === 0) {
        return null; // Don't show if no context
    }

    // Identify winners for highlighting
    const sortedByPrice = [...quotes].sort((a, b) => a.unit_price - b.unit_price);
    const bestPriceId = sortedByPrice[0]?.quote_id;

    const sortedBySpeed = [...quotes].sort((a, b) => a.delivery_days - b.delivery_days);
    const fastestId = sortedBySpeed[0]?.quote_id;

    return (
        <div className="bg-white rounded-lg shadow-md border border-indigo-100 mt-6 overflow-hidden">
            <div className="bg-gradient-to-r from-indigo-50 to-white px-6 py-4 border-b border-indigo-100">
                <h3 className="flex items-center gap-2 text-lg font-bold text-indigo-800">
                    <Trophy className="h-5 w-5 text-indigo-600" />
                    Live Quote Analysis
                    <span className="ml-2 px-2 py-0.5 text-xs font-semibold bg-white text-indigo-600 border border-indigo-200 rounded-full">
                        {quotes.length} Responses
                    </span>
                </h3>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
                        <tr>
                            <th className="px-6 py-3">Supplier</th>
                            <th className="px-6 py-3 text-center">Unit Price</th>
                            <th className="px-6 py-3 text-center">Delivery</th>
                            <th className="px-6 py-3 text-center">Reliability</th>
                            <th className="px-6 py-3 text-right">Availability</th>
                            <th className="px-6 py-3 text-right">Analysis</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {quotes.map((quote) => {
                            const isBestPrice = quote.quote_id === bestPriceId;
                            const isFastest = quote.quote_id === fastestId;

                            // Dynamic Row Styling based on value
                            let rowClass = "hover:bg-slate-50 transition-colors";
                            if (isBestPrice) rowClass += " bg-green-50/50";

                            return (
                                <tr key={quote.quote_id} className={rowClass}>
                                    <td className="px-6 py-4 font-medium text-gray-900">
                                        <div className="flex flex-col">
                                            <span>{quote.supplier_name}</span>
                                            <span className="text-xs text-slate-400">{quote.supplier_code}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-center font-bold text-slate-700">
                                        ${quote.unit_price.toFixed(2)}
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <div className="flex items-center justify-center gap-1 text-gray-600">
                                            <Clock className="h-3 w-3 text-slate-400" />
                                            {quote.delivery_days} Days
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${quote.reliability_score > 95 ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-600"
                                            }`}>
                                            {quote.reliability_score}%
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right text-gray-600">
                                        {quote.quantity_available.toLocaleString()} units
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex justify-end gap-2">
                                            {isBestPrice && (
                                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                                    <DollarSign className="h-3 w-3 mr-1" /> Best Value
                                                </span>
                                            )}
                                            {isFastest && (
                                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                                    <Clock className="h-3 w-3 mr-1" /> Fastest
                                                </span>
                                            )}
                                            {!isBestPrice && !isFastest && (
                                                <span className="text-xs text-slate-400 italic">Standard</span>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
