import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import axios from 'axios';

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
        const interval = setInterval(fetchDashboardData, 10000); // Refresh every 10s
        return () => clearInterval(interval);
    }, []);

    const fetchDashboardData = async () => {
        try {
            const [statsRes, agentRes, medicinesRes] = await Promise.all([
                axios.get(`${API_URL}/api/v1/dashboard/stats`),
                axios.get(`${API_URL}/api/v1/dashboard/agent-status`),
                axios.get(`${API_URL}/api/v1/inventory/medicines?low_stock_only=true`)
            ]);

            setStats(statsRes.data);
            setAgentStatus(agentRes.data);
            setLowStockMedicines(medicinesRes.data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            setLoading(false);
        }
    };

    const triggerProcurement = async (medicineId: number, quantity: number) => {
        try {
            await axios.post(`${API_URL}/api/v1/inventory/trigger-procurement`, {
                medicine_id: medicineId,
                quantity: quantity,
                urgency: 'HIGH'
            });
            alert('Procurement triggered successfully!');
            fetchDashboardData();
        } catch (error) {
            console.error('Error triggering procurement:', error);
            alert('Error triggering procurement');
        }
    };

    const getUrgencyColor = (level: string) => {
        switch (level) {
            case 'CRITICAL': return 'text-red-600 bg-red-100';
            case 'HIGH': return 'text-orange-600 bg-orange-100';
            case 'MEDIUM': return 'text-yellow-600 bg-yellow-100';
            default: return 'text-green-600 bg-green-100';
        }
    };

    const getAgentStatusColor = (status: string) => {
        return status === 'ACTIVE' ? 'text-green-600' : 'text-gray-400';
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-100 flex items-center justify-center">
                <div className="text-center">
                    <Clock className="w-12 h-12 animate-spin mx-auto text-blue-600" />
                    <p className="mt-4 text-gray-600">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-100 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">
                        Pharmacy Supply Chain AI
                    </h1>
                    <p className="text-gray-600 mt-2">
                        Autonomous procurement system powered by AI agents
                    </p>
                </div>

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
                        value={stats?.low_stock_items || 0}
                        icon={<TrendingUp className="w-6 h-6" />}
                        color="red"
                    />
                    <StatCard
                        title="Recent Orders"
                        value={stats?.recent_orders?.length || 0}
                        icon={<CheckCircle className="w-6 h-6" />}
                        color="green"
                    />
                </div>

                {/* Agent Status */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 className="text-xl font-semibold mb-4">Agent Status</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {agentStatus && Object.entries(agentStatus).map(([agent, status]) => (
                            <div key={agent} className="flex items-center space-x-3 p-4 bg-gray-50 rounded">
                                <Activity className={`w-5 h-5 ${getAgentStatusColor(status)}`} />
                                <div>
                                    <p className="text-sm text-gray-600 capitalize">{agent} Agent</p>
                                    <p className={`text-sm font-semibold ${getAgentStatusColor(status)}`}>
                                        {status}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Low Stock Medicines */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 className="text-xl font-semibold mb-4">Low Stock Alerts</h2>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Medicine
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Current Stock
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Days of Supply
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Urgency
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Action
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {lowStockMedicines.map((medicine) => (
                                    <tr key={medicine.id}>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div>
                                                <div className="text-sm font-medium text-gray-900">
                                                    {medicine.name}
                                                </div>
                                                <div className="text-sm text-gray-500">{medicine.dosage}</div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {medicine.current_stock.toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {medicine.days_of_supply.toFixed(1)} days
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 text-xs font-semibold rounded ${getUrgencyColor(medicine.urgency_level)}`}>
                                                {medicine.urgency_level}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            <button
                                                onClick={() => triggerProcurement(medicine.id, 5000)}
                                                className="text-blue-600 hover:text-blue-800 font-medium"
                                            >
                                                Trigger Procurement
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {lowStockMedicines.length === 0 && (
                            <div className="text-center py-8 text-gray-500">
                                No low stock items at the moment
                            </div>
                        )}
                    </div>
                </div>

                {/* Recent Orders */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-xl font-semibold mb-4">Recent Orders</h2>
                    <div className="space-y-3">
                        {stats?.recent_orders?.map((order, index) => (
                            <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded">
                                <div>
                                    <p className="font-medium text-gray-900">{order.po_number}</p>
                                    <p className="text-sm text-gray-500">
                                        {new Date(order.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="font-semibold text-gray-900">
                                        ${order.total_amount.toFixed(2)}
                                    </p>
                                    <p className="text-sm text-gray-500">{order.status}</p>
                                </div>
                            </div>
                        ))}
                        {(!stats?.recent_orders || stats.recent_orders.length === 0) && (
                            <div className="text-center py-8 text-gray-500">
                                No recent orders
                            </div>
                        )}
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
        green: 'bg-green-100 text-green-600',
    };

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-gray-600 text-sm">{title}</p>
                    <p className="text-3xl font-bold mt-2">{value}</p>
                </div>
                <div className={`p-3 rounded-full ${colorClasses[color as keyof typeof colorClasses]}`}>
                    {icon}
                </div>
            </div>
        </div>
    );
}

export default App;
