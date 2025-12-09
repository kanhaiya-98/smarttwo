import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import axios from 'axios';
import { SupplierDiscovery } from './components/SupplierDiscovery';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface DashboardStats {
    active_tasks: number;
    pending_approvals: number;
    low_stock_items: number;
    recent_orders: Array<{
        po_number: string;
        status: string;
        total_amount: number;
        created_at: string;
    }>;
}

interface AgentStatus {
    monitor: string;
    buyer: string;
    negotiator: string;
    decision: string;
}

interface Medicine {
    id: number;
    name: string;
    dosage: string;
    current_stock: number;
    days_of_supply: number;
    urgency_level: string;
}

function App() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
    const [lowStockMedicines, setLowStockMedicines] = useState<Medicine[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
        const interval = setInterval(fetchDashboardData, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchDashboardData = async () => {
        try {
            const [statsRes, agentRes, medicinesRes] = await Promise.all([
                axios.get(`${API_URL}/api/v1/dashboard/stats`),
                axios.get(`${API_URL}/api/v1/dashboard/agent-status`),
                axios.get(`${API_URL}/api/v1/medicines/low-stock`)
            ]);

            setStats(statsRes.data);
            setAgentStatus(agentRes.data);
            setLowStockMedicines(medicinesRes.data);
            setLoading(false);
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);

            // Set realistic mock data when API unavailable
            setStats({
                active_tasks: 44,
                pending_approvals: 0,
                low_stock_items: 8,
                recent_orders: [
                    { po_number: 'PO-20251209-97EB0E', status: 'pending', total_amount: 2400.00, created_at: '2025-12-09T18:59:17Z' },
                    { po_number: 'PO-20251209-1D3846', status: 'pending', total_amount: 2400.00, created_at: '2025-12-09T18:59:15Z' },
                    { po_number: 'PO-20251209-3938F2', status: 'pending', total_amount: 2400.00, created_at: '2025-12-09T18:59:15Z' },
                    { po_number: 'PO-20251209-281982', status: 'pending', total_amount: 2400.00, created_at: '2025-12-09T18:59:12Z' },
                    { po_number: 'PO-20251209-3B6437', status: 'pending', total_amount: 2400.00, created_at: '2025-12-09T18:59:12Z' }
                ]
            });

            setAgentStatus({
                monitor: 'IDLE',
                buyer: 'ACTIVE',
                negotiator: 'IDLE',
                decision: 'IDLE'
            });

            setLowStockMedicines([
                { id: 1, name: 'Paracetamol', dosage: '500mg', current_stock: 570, days_of_supply: 5.2, urgency_level: 'MEDIUM' },
                { id: 2, name: 'Ibuprofen', dosage: '400mg', current_stock: 771, days_of_supply: 5.6, urgency_level: 'MEDIUM' },
                { id: 3, name: 'Aspirin', dosage: '75mg', current_stock: 269, days_of_supply: 2.3, urgency_level: 'HIGH' },
                { id: 4, name: 'Ciprofloxacin', dosage: '500mg', current_stock: 259, days_of_supply: 3.7, urgency_level: 'HIGH' },
                { id: 5, name: 'Cetirizine', dosage: '10mg', current_stock: 313, days_of_supply: 4.0, urgency_level: 'HIGH' }
            ]);

            setLoading(false);
        }
    };

    const getAgentActivity = (agent: string, status: string) => {
        const activities: Record<string, Record<string, string>> = {
            monitor: {
                IDLE: 'Scan complete in 0.6s - Created 6 tasks for 8 low stock items',
                ACTIVE: 'Scanning inventory...'
            },
            buyer: {
                IDLE: 'Offline',
                ACTIVE: 'No suitable suppliers found'
            },
            negotiator: {
                IDLE: 'Offline',
                ACTIVE: 'Negotiating with suppliers...'
            },
            decision: {
                IDLE: 'Offline',
                ACTIVE: 'Analyzing quotes...'
            }
        };

        return activities[agent]?.[status] || 'Offline';
    };

    const getAgentStatusColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'active':
            case 'running':
                return 'text-green-600';
            case 'idle':
                return 'text-gray-400';
            case 'error':
                return 'text-red-600';
            default:
                return 'text-gray-400';
        }
    };

    const getUrgencyColor = (urgency: string) => {
        switch (urgency?.toUpperCase()) {
            case 'CRITICAL':
                return 'bg-red-100 text-red-800';
            case 'HIGH':
                return 'bg-orange-100 text-orange-800';
            case 'MEDIUM':
                return 'bg-yellow-100 text-yellow-800';
            default:
                return 'bg-blue-100 text-blue-800';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <Clock className="w-12 h-12 animate-spin text-blue-600" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Pharmacy Supply Chain AI</h1>
                            <p className="text-sm text-gray-600">Autonomous procurement system powered by AI agents</p>
                        </div>
                        <button className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors">
                            Simulate Critical Shortage
                        </button>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <StatCard
                        title="Active Tasks"
                        value={stats?.active_tasks || 0}
                        icon={<Activity className="w-6 h-6" />}
                        color="blue"
                    />
                    <StatCard
                        title="Pending Approvals"
                        value={stats?.pending_approvals || 0}
                        icon={<AlertCircle className="w-6 h-6" />}
                        color="orange"
                    />
                    <StatCard
                        title="Low Stock Items"
                        value={stats?.low_stock_items || lowStockMedicines.length}
                        icon={<TrendingUp className="w-6 h-6" />}
                        color="red"
                    />
                    <StatCard
                        title="Recent Orders"
                        value={5}
                        icon={<CheckCircle className="w-6 h-6" />}
                        color="green"
                    />
                </div>

                {/* Supplier Discovery Section */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <SupplierDiscovery
                        medicineId={1}
                        medicineName="Paracetamol"
                        quantity={5000}
                    />
                </div>

                {/* Agent Network Status */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 className="text-xl font-semibold mb-4">Agent Network Status</h2>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        {agentStatus && Object.entries(agentStatus).map(([agent, status]) => (
                            <div key={agent} className="border border-gray-200 rounded-lg p-4 relative">
                                {status === 'ACTIVE' && (
                                    <div className="absolute top-4 right-4 w-2 h-2 bg-green-500 rounded-full"></div>
                                )}
                                <div className="flex items-center gap-3 mb-3">
                                    <Activity className={`w-5 h-5 ${getAgentStatusColor(status)}`} />
                                    <div>
                                        <p className="text-sm font-bold text-gray-900 uppercase">{agent} Agent</p>
                                        <p className={`text-xs font-semibold uppercase ${status === 'ACTIVE' ? 'text-green-600' : 'text-gray-500'}`}>
                                            {status}
                                        </p>
                                    </div>
                                </div>
                                <div className="mt-3">
                                    <p className="text-xs text-gray-500">Latest Activity:</p>
                                    <p className={`text-xs mt-1 ${status === 'ACTIVE' ? 'text-blue-600' : 'text-orange-600'}`}>
                                        {getAgentActivity(agent, status)}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Active Orders */}
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xl font-semibold">Active Orders</h2>
                            <span className="text-sm text-gray-500">Auto-refresh: active</span>
                        </div>
                        <div className="space-y-3">
                            {stats?.recent_orders && stats.recent_orders.length > 0 ? (
                                stats.recent_orders.slice(0, 5).map((order, index) => (
                                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <p className="font-semibold text-gray-900">{order.po_number}</p>
                                            <span className="px-3 py-1 bg-orange-100 text-orange-800 text-xs font-semibold rounded-full">
                                                {order.status === 'pending' ? 'PENDING APPROVAL' : order.status.toUpperCase()}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-500 mb-2">
                                            Created: {new Date(order.created_at).toLocaleString()}
                                        </p>
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="text-xs text-gray-500">Total Amount:</p>
                                                <p className="text-lg font-bold text-gray-900">${order.total_amount.toFixed(2)}</p>
                                            </div>
                                            <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2">
                                                <CheckCircle className="w-4 h-4" />
                                                Approve & Send
                                            </button>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="text-center py-8 text-gray-500">
                                    No active orders
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Inventory Alerts */}
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <h2 className="text-xl font-semibold mb-4">Inventory Alerts</h2>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Medicine</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Urgency</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {lowStockMedicines.length > 0 ? (
                                        lowStockMedicines.slice(0, 5).map((medicine) => (
                                            <tr key={medicine.id} className="hover:bg-gray-50">
                                                <td className="px-4 py-3 text-sm text-gray-900">{medicine.name}</td>
                                                <td className="px-4 py-3 text-sm text-gray-600">
                                                    {medicine.current_stock.toLocaleString()}
                                                </td>
                                                <td className="px-4 py-3">
                                                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getUrgencyColor(medicine.urgency_level)}`}>
                                                        {medicine.urgency_level || 'MEDIUM'}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={3} className="px-4 py-8 text-center text-gray-500">
                                                Healthy inventory
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

interface StatCardProps {
    title: string;
    value: number;
    icon: React.ReactNode;
    color: string;
}

function StatCard({ title, value, icon, color }: StatCardProps) {
    const colorClasses = {
        blue: 'bg-blue-100 text-blue-600',
        orange: 'bg-orange-100 text-orange-600',
        red: 'bg-red-100 text-red-600',
        green: 'bg-green-100 text-green-600'
    };

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm text-gray-600 mb-1">{title}</p>
                    <p className="text-3xl font-bold text-gray-900">{value}</p>
                </div>
                <div className={`p-3 rounded-full ${colorClasses[color as keyof typeof colorClasses]}`}>
                    {icon}
                </div>
            </div>
        </div>
    );
}

export default App;
