import React, { useState, useEffect } from 'react';
import { Activity, Mail, MessageSquare, Brain, CheckCircle, TrendingUp, Clock, DollarSign } from 'lucide-react';

interface AgentStatus {
    name: string;
    status: 'idle' | 'active' | 'completed' | 'error';
    currentTask?: string;
    icon: React.ReactNode;
    color: string;
}

const AgentWorkflowDashboard: React.FC = () => {
    const [agents, setAgents] = useState<AgentStatus[]>([
        {
            name: 'Email Monitor',
            status: 'active',
            currentTask: 'Checking inbox every 5 minutes',
            icon: <Mail className="w-6 h-6" />,
            color: 'blue'
        },
        {
            name: 'Quote Collector',
            status: 'idle',
            currentTask: 'Waiting for supplier responses',
            icon: <Activity className="w-6 h-6" />,
            color: 'purple'
        },
        {
            name: 'Negotiator Agent',
            status: 'idle',
            currentTask: 'Ready to negotiate',
            icon: <MessageSquare className="w-6 h-6" />,
            color: 'orange'
        },
        {
            name: 'Decision Agent',
            status: 'idle',
            currentTask: 'Awaiting quotes',
            icon: <Brain className="w-6 h-6" />,
            color: 'green'
        },
        {
            name: 'Approval System',
            status: 'idle',
            currentTask: 'No pending approvals',
            icon: <CheckCircle className="w-6 h-6" />,
            color: 'teal'
        }
    ]);

    const [stats, setStats] = useState({
        emailsChecked: 0,
        quotesReceived: 0,
        negotiationsActive: 0,
        pendingApprovals: 0,
        ordersPlaced: 0
    });

    useEffect(() => {
        // Fetch agent status from API
        const fetchAgentStatus = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/v1/dashboard/stats');
                const data = await response.json();

                setStats({
                    emailsChecked: data.emails_checked || 0,
                    quotesReceived: data.quotes_received || 0,
                    negotiationsActive: data.active_negotiations || 0,
                    pendingApprovals: data.pending_approvals || 0,
                    ordersPlaced: data.orders_placed || 0
                });
            } catch (error) {
                console.error('Error fetching agent status:', error);
            }
        };

        fetchAgentStatus();
        const interval = setInterval(fetchAgentStatus, 5000); // Update every 5 seconds

        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'bg-green-500 animate-pulse';
            case 'completed': return 'bg-blue-500';
            case 'error': return 'bg-red-500';
            default: return 'bg-gray-400';
        }
    };

    const getAgentColor = (color: string) => {
        const colors: Record<string, string> = {
            blue: 'from-blue-500 to-blue-700',
            purple: 'from-purple-500 to-purple-700',
            orange: 'from-orange-500 to-orange-700',
            green: 'from-green-500 to-green-700',
            teal: 'from-teal-500 to-teal-700'
        };
        return colors[color] || 'from-gray-500 to-gray-700';
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-4xl font-bold text-white mb-2">
                    🤖 Autonomous Procurement System
                </h1>
                <p className="text-purple-200">
                    Real-time AI Agent Workflow Visualization
                </p>
            </div>

            {/* Stats Bar */}
            <div className="grid grid-cols-5 gap-4 mb-8">
                <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl p-6 text-white transform hover:scale-105 transition-transform">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-blue-100 text-sm">Emails Checked</p>
                            <p className="text-3xl font-bold">{stats.emailsChecked}</p>
                        </div>
                        <Mail className="w-12 h-12 opacity-50" />
                    </div>
                </div>

                <div className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-xl p-6 text-white transform hover:scale-105 transition-transform">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-purple-100 text-sm">Quotes Received</p>
                            <p className="text-3xl font-bold">{stats.quotesReceived}</p>
                        </div>
                        <TrendingUp className="w-12 h-12 opacity-50" />
                    </div>
                </div>

                <div className="bg-gradient-to-br from-orange-600 to-orange-800 rounded-xl p-6 text-white transform hover:scale-105 transition-transform">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-orange-100 text-sm">Active Negotiations</p>
                            <p className="text-3xl font-bold">{stats.negotiationsActive}</p>
                        </div>
                        <MessageSquare className="w-12 h-12 opacity-50" />
                    </div>
                </div>

                <div className="bg-gradient-to-br from-teal-600 to-teal-800 rounded-xl p-6 text-white transform hover:scale-105 transition-transform">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-teal-100 text-sm">Pending Approvals</p>
                            <p className="text-3xl font-bold">{stats.pendingApprovals}</p>
                        </div>
                        <Clock className="w-12 h-12 opacity-50" />
                    </div>
                </div>

                <div className="bg-gradient-to-br from-green-600 to-green-800 rounded-xl p-6 text-white transform hover:scale-105 transition-transform">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-green-100 text-sm">Orders Placed</p>
                            <p className="text-3xl font-bold">{stats.ordersPlaced}</p>
                        </div>
                        <CheckCircle className="w-12 h-12 opacity-50" />
                    </div>
                </div>
            </div>

            {/* Agent Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {agents.map((agent, index) => (
                    <div
                        key={index}
                        className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:border-white/40 transition-all transform hover:scale-105 cursor-pointer"
                        onClick={() => {
                            // Navigate to agent detail view
                            console.log(`Clicked on ${agent.name}`);
                        }}
                    >
                        <div className="flex items-start justify-between mb-4">
                            <div className={`p-3 rounded-xl bg-gradient-to-br ${getAgentColor(agent.color)}`}>
                                {agent.icon}
                            </div>
                            <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                        </div>

                        <h3 className="text-xl font-bold text-white mb-2">{agent.name}</h3>
                        <p className="text-gray-300 text-sm mb-4">{agent.currentTask}</p>

                        <div className="flex items-center space-x-2">
                            <div className="flex-1 bg-gray-700 rounded-full h-2">
                                <div
                                    className={`h-2 rounded-full bg-gradient-to-r ${getAgentColor(agent.color)} transition-all`}
                                    style={{ width: agent.status === 'active' ? '60%' : '0%' }}
                                />
                            </div>
                            <span className="text-xs text-gray-400 capitalize">{agent.status}</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Workflow Timeline */}
            <div className="mt-12 bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
                <h2 className="text-2xl font-bold text-white mb-6">Workflow Pipeline</h2>

                <div className="relative">
                    {/* Timeline Line */}
                    <div className="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-500 via-purple-500 to-green-500" />

                    {/* Timeline Steps */}
                    <div className="space-y-8">
                        {[
                            { step: 1, title: 'Email Monitoring', desc: 'Check Gmail inbox every 5 minutes', status: 'active' },
                            { step: 2, title: 'Quote Parsing', desc: 'AI extracts price, delivery, stock', status: 'waiting' },
                            { step: 3, title: 'Negotiation', desc: 'Multi-round AI negotiation (max 3)', status: 'waiting' },
                            { step: 4, title: 'Decision Making', desc: 'Weighted scoring + Gemini reasoning', status: 'waiting' },
                            { step: 5, title: 'Approval', desc: 'Auto-approve <$1K or manual review', status: 'waiting' },
                            { step: 6, title: 'Order Placement', desc: 'PO generation and tracking', status: 'waiting' }
                        ].map((item) => (
                            <div key={item.step} className="flex items-start space-x-4 relative">
                                <div className={`w-16 h-16 rounded-full flex items-center justify-center font-bold text-xl z-10 ${item.status === 'active'
                                        ? 'bg-gradient-to-br from-green-400 to-green-600 text-white animate-pulse'
                                        : 'bg-gradient-to-br from-gray-600 to-gray-800 text-gray-300'
                                    }`}>
                                    {item.step}
                                </div>
                                <div className="flex-1">
                                    <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                                    <p className="text-gray-400 text-sm">{item.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AgentWorkflowDashboard;
