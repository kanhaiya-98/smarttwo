import React, { useState, useEffect, useRef } from 'react';
import { X, Activity, AlertCircle, CheckCircle, Info, Clock, Filter } from 'lucide-react';

// Use environment variable or window global, fallback to localhost
const API_URL = (typeof window !== 'undefined' && (window as any).VITE_API_URL) || import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface AgentActivityModalProps {
    agentName: string;
    onClose: () => void;
}

interface ActivityLog {
    id: number;
    agent_name: string;
    action_type: string;
    message: string;
    status: string;
    metadata?: any;
    created_at: string;
}

interface AgentStats {
    agent: string;
    total_activities_24h: number;
    successful_actions: number;
    warnings: number;
    errors: number;
}

const AgentActivityModal: React.FC<AgentActivityModalProps> = ({ agentName, onClose }) => {
    const [activities, setActivities] = useState<ActivityLog[]>([]);
    const [stats, setStats] = useState<AgentStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [filterType, setFilterType] = useState('ALL');
    const [isActive, setIsActive] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchActivities();
        fetchStats();

        const interval = setInterval(() => {
            fetchActivities();
            fetchStats();
        }, 3000);

        return () => clearInterval(interval);
    }, [agentName, filterType]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [activities]);

    const fetchActivities = async () => {
        try {
            const params = filterType !== 'ALL' ? `?action_type=${filterType}` : '';
            const response = await fetch(`${API_URL}/api/v1/agents/activity/${agentName}${params}`);
            if (!response.ok) throw new Error('Failed to fetch activity');
            const data = await response.json();
            setActivities(data);

            if (data.length > 0) {
                const latestTime = new Date(data[0].created_at);
                const twoMinutesAgo = new Date(Date.now() - 2 * 60 * 1000);
                setIsActive(latestTime > twoMinutesAgo);
            }

            setLoading(false);
        } catch (error) {
            console.error('Error fetching activities:', error);
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const response = await fetch(`${API_URL}/api/v1/agents/stats`);
            if (!response.ok) throw new Error('Failed to fetch stats');
            const data = await response.json();
            const agentStats = data.find((s: AgentStats) => s.agent === agentName);
            setStats(agentStats);
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'SUCCESS':
                return <CheckCircle className="w-4 h-4 text-green-400" />;
            case 'WARNING':
                return <AlertCircle className="w-4 h-4 text-yellow-400" />;
            case 'ERROR':
                return <AlertCircle className="w-4 h-4 text-red-400" />;
            default:
                return <Info className="w-4 h-4 text-blue-400" />;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'SUCCESS':
                return 'text-green-400';
            case 'WARNING':
                return 'text-yellow-400';
            case 'ERROR':
                return 'text-red-400';
            default:
                return 'text-blue-400';
        }
    };

    const formatTimestamp = (timestamp: string) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;

        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;

        return date.toLocaleDateString();
    };

    const actionTypes = ['ALL', 'SCAN', 'DETECT', 'ALERT', 'FORECAST', 'CREATE_TASK', 'ERROR'];

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-900 rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
                <div className="border-b border-gray-700 p-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="relative">
                            <Activity className="w-6 h-6 text-green-400" />
                            {isActive && (
                                <span className="absolute -top-1 -right-1 w-3 h-3">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-3 w-3 bg-green-400"></span>
                                </span>
                            )}
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">{agentName} Agent</h2>
                            <p className="text-sm text-gray-400">{isActive ? 'Active' : 'Idle'} • Real-time Activity Feed</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {stats && (
                    <div className="border-b border-gray-700 p-4 bg-gray-800">
                        <div className="grid grid-cols-4 gap-4 text-center">
                            <div>
                                <p className="text-2xl font-bold text-white">{stats.total_activities_24h}</p>
                                <p className="text-xs text-gray-400">Total (24h)</p>
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-green-400">{stats.successful_actions}</p>
                                <p className="text-xs text-gray-400">Success</p>
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-yellow-400">{stats.warnings}</p>
                                <p className="text-xs text-gray-400">Warnings</p>
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-red-400">{stats.errors}</p>
                                <p className="text-xs text-gray-400">Errors</p>
                            </div>
                        </div>
                    </div>
                )}

                <div className="border-b border-gray-700 p-3 bg-gray-800 flex items-center space-x-2 overflow-x-auto">
                    <Filter className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <div className="flex space-x-2">
                        {actionTypes.map(type => (
                            <button
                                key={type}
                                onClick={() => setFilterType(type)}
                                className={`px-3 py-1 rounded text-xs font-medium transition-colors whitespace-nowrap ${filterType === type
                                        ? 'bg-green-500 text-white'
                                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                    }`}
                            >
                                {type}
                            </button>
                        ))}
                    </div>
                </div>

                <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 bg-black font-mono text-sm space-y-2">
                    {loading ? (
                        <div className="flex items-center justify-center h-full">
                            <Clock className="w-8 h-8 animate-spin text-green-400" />
                        </div>
                    ) : activities.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500">
                            <Activity className="w-12 h-12 mb-2" />
                            <p>No activity recorded yet</p>
                        </div>
                    ) : (
                        activities.map((activity) => (
                            <div key={activity.id} className="flex items-start space-x-3 p-2 hover:bg-gray-900 rounded transition-colors">
                                <div className="flex-shrink-0 mt-1">{getStatusIcon(activity.status)}</div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center space-x-2">
                                        <span className="text-gray-500 text-xs">{formatTimestamp(activity.created_at)}</span>
                                        <span className="text-gray-600 text-xs">[{activity.action_type}]</span>
                                    </div>
                                    <p className={`${getStatusColor(activity.status)} break-words`}>{activity.message}</p>
                                    {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                                        <details className="mt-1">
                                            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">Metadata</summary>
                                            <pre className="text-xs text-gray-600 mt-1 p-2 bg-gray-900 rounded overflow-x-auto">
                                                {JSON.stringify(activity.metadata, null, 2)}
                                            </pre>
                                        </details>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>

                <div className="border-t border-gray-700 p-3 bg-gray-800 flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-xs text-gray-400">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        <span>Auto-refreshing every 3 seconds</span>
                    </div>
                    <button onClick={fetchActivities} className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded transition-colors">
                        Refresh Now
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AgentActivityModal;
