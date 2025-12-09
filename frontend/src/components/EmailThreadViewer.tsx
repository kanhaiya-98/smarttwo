// Enhanced email thread viewer with one-liner summaries
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Mail, ArrowRight, CheckCircle, Clock } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface EmailMessage {
    id: number;
    sender: string;
    recipient: string;
    subject: string;
    body: string;
    is_from_agent: boolean;
    quoted_price: number | null;
    delivery_days: number | null;
    timestamp: string;
}

interface EmailThreadViewerProps {
    supplierId: number;
    supplierName: string;
    onClose: () => void;
}

export const EmailThreadViewer: React.FC<EmailThreadViewerProps> = ({
    supplierId,
    supplierName,
    onClose
}) => {
    const [messages, setMessages] = useState<EmailMessage[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchEmails();
    }, [supplierId]);

    const fetchEmails = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/v1/discovery/emails/${supplierId}`);
            setMessages(response.data);
            setLoading(false);
        } catch (error) {
            console.error('Failed to fetch emails:', error);
            setLoading(false);
        }
    };

    const generateOneLiner = (msg: EmailMessage): string => {
        if (msg.is_from_agent) {
            // Our message
            if (msg.body.includes('quotation') || msg.body.includes('best quotation')) {
                return `AI: Requesting quote for medicine - urgent procurement needed`;
            } else if (msg.body.includes('match') || msg.body.includes('competitive')) {
                return `AI: Negotiating - Can you match ${msg.quoted_price ? '$' + msg.quoted_price : 'competitor price'}?`;
            } else {
                return `AI: Follow-up on pricing and delivery terms`;
            }
        } else {
            // Supplier response
            if (msg.quoted_price && msg.delivery_days) {
                return `Supplier: Quote ${msg.quoted_price}/unit, ${msg.delivery_days} days delivery`;
            } else {
                return `Supplier: Response received - reviewing terms`;
            }
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="border-b p-4 flex justify-between items-center bg-gradient-to-r from-blue-50 to-purple-50">
                    <div>
                        <h3 className="font-bold text-lg text-gray-900">{supplierName}</h3>
                        <p className="text-sm text-gray-600">Email Conversation Thread</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-500 hover:text-gray-700 transition-colors"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-3">
                    {loading ? (
                        <div className="text-center py-8 text-gray-500">
                            <Clock className="w-8 h-8 animate-spin mx-auto mb-2" />
                            Loading conversation...
                        </div>
                    ) : messages.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <Mail className="w-12 h-12 mx-auto mb-3 opacity-30" />
                            <p>No messages yet</p>
                        </div>
                    ) : (
                        messages.map((msg, index) => (
                            <div
                                key={msg.id}
                                className={`flex items-start gap-3 p-4 rounded-lg transition-all ${msg.is_from_agent
                                    ? 'bg-blue-50 border-l-4 border-blue-500'
                                    : 'bg-green-50 border-l-4 border-green-500'
                                    }`}
                            >
                                <div className="flex-shrink-0 mt-1">
                                    {msg.is_from_agent ? (
                                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                                            AI
                                        </div>
                                    ) : (
                                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                                            S
                                        </div>
                                    )}
                                </div>

                                <div className="flex-1">
                                    <p className={`font-medium ${msg.is_from_agent ? 'text-blue-900' : 'text-green-900'}`}>
                                        {generateOneLiner(msg)}
                                    </p>

                                    {/* Show key details if available */}
                                    {!msg.is_from_agent && (msg.quoted_price || msg.delivery_days) && (
                                        <div className="mt-2 flex gap-4 text-sm">
                                            {msg.quoted_price && (
                                                <span className="bg-white px-2 py-1 rounded font-mono text-green-700">
                                                    Price: ${msg.quoted_price}/unit
                                                </span>
                                            )}
                                            {msg.delivery_days && (
                                                <span className="bg-white px-2 py-1 rounded font-mono text-blue-700">
                                                    Delivery: {msg.delivery_days} days
                                                </span>
                                            )}
                                        </div>
                                    )}

                                    <p className="text-xs text-gray-500 mt-1">
                                        {new Date(msg.timestamp).toLocaleString()}
                                    </p>
                                </div>

                                {index < messages.length - 1 && (
                                    <ArrowRight className="w-4 h-4 text-gray-400 mt-2" />
                                )}
                            </div>
                        ))
                    )}
                </div>

                {/* Footer with status */}
                <div className="border-t p-4 bg-gray-50">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span>{messages.length} messages exchanged</span>
                        </div>
                        <button
                            onClick={onClose}
                            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm font-medium transition-colors"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
