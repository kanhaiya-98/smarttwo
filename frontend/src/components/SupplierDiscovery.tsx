import React, { useState } from 'react';
import { Search, Mail, Check, ExternalLink, Loader2 } from 'lucide-react';
import axios from 'axios';
import { EmailThreadViewer } from './EmailThreadViewer';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Supplier {
    id: number;
    name: string;
    website: string;
    email: string;
    location: string;
    status: string;
    emails_sent: number;
    emails_received: number;
    last_activity: string;
}

interface DiscoveryProps {
    medicineId: number;
    medicineName: string;
    quantity: number;
}

export const SupplierDiscovery: React.FC<DiscoveryProps> = ({
    medicineId,
    medicineName,
    quantity
}) => {
    const [discovering, setDiscovering] = useState(false);
    const [suppliers, setSuppliers] = useState<Supplier[]>([]);
    const [stage, setStage] = useState<'idle' | 'searching' | 'found' | 'complete'>('idle');
    const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
    const [sendingEmail, setSendingEmail] = useState<number | null>(null);
    const [emailSentIds, setEmailSentIds] = useState<Set<number>>(new Set());

    const handleDiscover = async () => {
        setDiscovering(true);
        setStage('searching');
        setEmailSentIds(new Set()); // Reset email sent tracking

        try {
            await axios.post(`${API_URL}/api/v1/discovery/start`, {
                medicine_id: medicineId,
                quantity: quantity
            });

            setStage('found');

            setTimeout(async () => {
                const suppliersResp = await axios.get(`${API_URL}/api/v1/discovery/suppliers/${medicineId}`);
                setSuppliers(suppliersResp.data);
                setStage('complete');
                setDiscovering(false);
            }, 1000);

        } catch (error) {
            console.error('Discovery failed:', error);
            setDiscovering(false);
            setStage('idle');
        }
    };

    const handleSendEmail = async (supplierId: number) => {
        setSendingEmail(supplierId);

        try {
            const response = await axios.post(
                `${API_URL}/api/v1/discovery/send-email/${supplierId}`,
                null,
                { params: { quantity: quantity } }
            );

            if (response.data.status === 'success') {
                // Mark this supplier as email sent
                setEmailSentIds(prev => new Set([...prev, supplierId]));

                // Update supplier in list
                setSuppliers(suppliers.map(s =>
                    s.id === supplierId ? { ...s, status: 'EMAIL_SENT', emails_sent: s.emails_sent + 1 } : s
                ));
            }
        } catch (error) {
            console.error('Failed to send email:', error);
            alert('Failed to send email. Please try again.');
        } finally {
            setSendingEmail(null);
        }
    };

    const isEmailSent = (supplier: Supplier) => {
        return emailSentIds.has(supplier.id) || supplier.emails_sent > 0;
    };

    const topSuppliers = suppliers.slice(0, 5);

    return (
        <div className="space-y-6">
            <div className="text-center">
                <button
                    onClick={handleDiscover}
                    disabled={discovering}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Search className="w-6 h-6 inline mr-2" />
                    {discovering ? 'Discovering...' : 'Discover Best Suppliers'}
                </button>
            </div>

            {discovering && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                    {stage === 'searching' && (
                        <div className="animate-pulse text-blue-700">
                            Searching Google for {medicineName} suppliers...
                        </div>
                    )}
                    {stage === 'found' && (
                        <div className="text-green-600">
                            Found suppliers! Loading details...
                        </div>
                    )}
                </div>
            )}

            {suppliers.length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                    <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                        <h3 className="text-lg font-bold text-gray-900">Discovered Suppliers</h3>
                        <p className="text-sm text-gray-600 mt-1">
                            Showing top {topSuppliers.length} of {suppliers.length} pharmaceutical suppliers
                        </p>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Website</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Contact Email</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Send Quote Request</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {topSuppliers.map((supplier) => (
                                    <tr key={supplier.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4">
                                            <div className="font-medium text-gray-900">{supplier.name}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <a
                                                href={supplier.website}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                                            >
                                                <ExternalLink className="w-4 h-4" />
                                                <span className="text-sm">{supplier.website.replace('https://', '').substring(0, 30)}</span>
                                            </a>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="font-mono text-sm text-gray-700">{supplier.email}</span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-600">{supplier.location}</td>
                                        <td className="px-6 py-4">
                                            {isEmailSent(supplier) ? (
                                                <div className="flex items-center gap-2 text-green-600">
                                                    <Check className="w-5 h-5" />
                                                    <span className="text-sm font-medium">Email Sent</span>
                                                </div>
                                            ) : (
                                                <button
                                                    onClick={() => handleSendEmail(supplier.id)}
                                                    disabled={sendingEmail === supplier.id}
                                                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                                                >
                                                    {sendingEmail === supplier.id ? (
                                                        <>
                                                            <Loader2 className="w-4 h-4 animate-spin" />
                                                            Sending...
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Mail className="w-4 h-4" />
                                                            Send Email
                                                        </>
                                                    )}
                                                </button>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={() => setSelectedSupplier(supplier)}
                                                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                            >
                                                View Emails
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {selectedSupplier && (
                <EmailThreadViewer
                    supplierId={selectedSupplier.id}
                    supplierName={selectedSupplier.name}
                    onClose={() => setSelectedSupplier(null)}
                />
            )}
        </div>
    );
};
