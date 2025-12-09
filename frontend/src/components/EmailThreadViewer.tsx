// Enhanced email thread viewer with one-liner summaries
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Mail, ArrowRight, CheckCircle, Clock } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface EmailMessage {
    id: number;
    subject: string;
    body: string;
    is_from_agent: boolean;
    display_sender: string;
    display_recipient: string;
    quoted_price: number | null;
    delivery_days: number | null;
    created_at: string;
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
    const [emails, setEmails] = useState<EmailMessage[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchEmails();
    }, [supplierId]);

    const fetchEmails = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/v1/discovery/emails/${supplierId}`);
            setEmails(response.data);
        } catch (error) {
            console.error('Failed to fetch emails:', error);
        } finally {
            setLoading(false);
        }
    };

    const getOneLinerSummary = (email: EmailMessage): string => {
        if (email.is_from_agent) {
            // AI-sent message
            if (email.subject.toLowerCase().includes('quote request')) {
                return 'Requesting quote for medicine - urgent procurement needed';
            } else if (email.subject.toLowerCase().includes('negotiation')) {
                return 'Negotiating better pricing and delivery terms';
            } else {
                return 'Requesting information from supplier';
            }
        } else {
            // Supplier response
            if (email.quoted_price && email.delivery_days) {
                return `Quote $${email.quoted_price.toFixed(2)}/unit, ${email.delivery_days} days delivery`;
            } else if (email.quoted_price) {
                return `Quote $${email.quoted_price.toFixed(2)}/unit`;
            } else {
                return 'Response received';
            }
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="border-b p-6 flex justify-between items-center bg-gradient-to-r from-blue-50 to-purple-50">
                    <div>
                        <h3 className="font-bold text-xl text-gray-900">{supplierName}</h3>
                        <p className="text-sm text-gray-600 mt-1">Email Conversation Thread</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-500 hover:text-gray-700 p-2 rounded-full hover:bg-gray-100 transition-colors"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Email Thread */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <Clock className="w-8 h-8 animate-spin text-blue-600" />
                        </div>
                    ) : emails.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <Mail className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                            <p>No email conversations yet</p>
                        </div>
                    ) : (
                        emails.map((email) => (
                            <div
                                key={email.id}
                                className={`flex items-start gap-4 p-4 rounded-lg ${email.is_from_agent
                                        ? 'bg-blue-50 border-l-4 border-blue-500'
                                        : 'bg-green-50 border-l-4 border-green-500'
                                    }`}
                            >
                                <div className="flex-shrink-0">
                                    {email.is_from_agent ? (
                                        <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
                                            AI
                                        </div>
                                    ) : (
                                        <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center text-white font-bold">
                                            📦
                                        </div>
                                    )}
                                </div>

                                <div className="flex-1">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="font-semibold text-gray-900">
                                            {email.is_from_agent ? 'AI Agent' : supplierName}
                                        </span>
                                        <span className="text-xs text-gray-500">
                                            {new Date(email.created_at).toLocaleDateString()}
                                        </span>
                                    </div>

                                    {/* One-liner summary */}
                                    <div className="text-sm text-gray-700 font-medium mb-2">
                                        {getOneLinerSummary(email)}
                                    </div>

                                    {/* Quote details if present */}
                                    {!email.is_from_agent && (email.quoted_price || email.delivery_days) && (
                                        <div className="flex gap-3 mt-3">
                                            {email.quoted_price && (
                                                <div className="bg-white px-3 py-1.5 rounded-full border border-green-300">
                                                    <span className="text-xs text-gray-600">Price:</span>
                                                    <span className="text-sm font-bold text-green-700 ml-1">
                                                        ${email.quoted_price.toFixed(2)}/unit
                                                    </span>
                                                </div>
                                            )}
                                            {email.delivery_days && (
                                                <div className="bg-white px-3 py-1.5 rounded-full border border-blue-300">
                                                    <span className="text-xs text-gray-600">Delivery:</span>
                                                    <span className="text-sm font-bold text-blue-700 ml-1">
                                                        {email.delivery_days} days
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                <ArrowRight className="w-5 h-5 text-gray-400 flex-shrink-0 mt-2" />
                            </div>
                        ))
                    )}
                </div>

                {/* Footer */}
                <div className="border-t p-4 bg-gray-50 flex justify-between items-center">
                    <p className="text-sm text-gray-600">
                        {emails.length} {emails.length === 1 ? 'message' : 'messages'} in thread
                    </p>
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};
