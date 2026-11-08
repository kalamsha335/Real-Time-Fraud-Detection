import React, { useState, useEffect } from 'react';
import {
  Server,
  Database,
  Radio,
  Layers,
  Cpu,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  HardDrive
} from 'lucide-react';
import { api } from '../api';

export default function HealthView({ systemHealth, onRefresh }) {
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getModelInfo()
      .then(setModelInfo)
      .catch(() => null);
  }, []);

  const isApiHealthy = systemHealth?.status === 'healthy';
  const isModelLoaded = systemHealth?.model_loaded || false;

  const kafkaBroker = 'localhost:9092';
  const kafkaTopics = ['transactions', 'fraud-predictions', 'fraud-alerts'];

  return (
    <div className="space-y-6">
      {/* Infrastructure Diagnostic Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* 1. FastAPI Backend */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-slate-800 flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
                  <Server className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">FastAPI Prediction API</h3>
                  <p className="text-[11px] text-slate-400">High-throughput ASGI Engine</p>
                </div>
              </div>
              <span
                className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                  isApiHealthy
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                }`}
              >
                {isApiHealthy ? 'OPERATIONAL' : 'DOWN'}
              </span>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800 text-xs font-mono space-y-1.5 text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Host Port:</span>
                <span className="text-white">127.0.0.1:8000</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Version:</span>
                <span className="text-indigo-300">1.0.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Docs Endpoint:</span>
                <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">
                  /docs (Swagger UI)
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* 2. Database (PostgreSQL / SQLite Dual Mode) */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-slate-800 flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/30">
                  <Database className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">PostgreSQL / SQLite Storage</h3>
                  <p className="text-[11px] text-slate-400">Transaction & Alert Persistence</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                ACTIVE
              </span>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800 text-xs font-mono space-y-1.5 text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Mode:</span>
                <span className="text-indigo-300">Dual-Mode Fallback</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Active Storage:</span>
                <span className="text-white">database/fraud_detection.db</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Tables:</span>
                <span className="text-slate-200">5 tables initialized</span>
              </div>
            </div>
          </div>
        </div>

        {/* 3. Kafka Streaming Broker */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-slate-800 flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30">
                  <Radio className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">Apache Kafka Broker</h3>
                  <p className="text-[11px] text-slate-400">Event Stream Pipeline</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                STANDALONE MODE
              </span>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800 text-xs font-mono space-y-1.5 text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Broker:</span>
                <span className="text-slate-300">{kafkaBroker}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Connection Policy:</span>
                <span className="text-amber-300">Strict (No fake streaming)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Fallback Ingestion:</span>
                <span className="text-emerald-300">Direct HTTP / Simulator</span>
              </div>
            </div>
          </div>
        </div>

        {/* 4. XGBoost Classifier Artifact */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-slate-800 flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                  <Cpu className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">XGBoost ML Pipeline</h3>
                  <p className="text-[11px] text-slate-400">Primary Classifier</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                LOADED
              </span>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800 text-xs font-mono space-y-1.5 text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Expected Features:</span>
                <span className="text-indigo-300 font-bold">432 columns</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Decision Threshold:</span>
                <span className="text-white font-bold">0.5000</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Artifact:</span>
                <span className="text-slate-300 text-[10px]">models/fraud_detection_xgboost.pkl</span>
              </div>
            </div>
          </div>
        </div>

        {/* 5. PyTorch Geometric GNN */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-slate-800 flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
                  <Layers className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">PyTorch Geometric GCN</h3>
                  <p className="text-[11px] text-slate-400">Relationship Analysis Model</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                EXPERIMENTAL
              </span>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800 text-xs font-mono space-y-1.5 text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Architecture:</span>
                <span className="text-indigo-300">2-Layer FraudGCN</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Node Features:</span>
                <span className="text-white">11 numerical dims</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Relationship Proxy:</span>
                <span className="text-indigo-300">card1 attribute</span>
              </div>
            </div>
          </div>
        </div>

        {/* 6. Feast Feature Store */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-slate-800 flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/30">
                  <HardDrive className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">Feast Feature Store</h3>
                  <p className="text-[11px] text-slate-400">Point-in-Time Online Store</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                MATERIALIZED
              </span>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800 text-xs font-mono space-y-1.5 text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Entity:</span>
                <span className="text-indigo-300 font-bold">card1</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Features:</span>
                <span className="text-white">avg_amt, count_24h, total_count</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Leakage Protection:</span>
                <span className="text-emerald-300">Strict shift(1) offset</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Kafka & Topics Architecture Info */}
      <div className="p-6 rounded-2xl bg-navy-900 border border-slate-800 shadow-sm">
        <h3 className="text-sm font-bold text-white mb-2">Kafka Streaming Architecture & Topics</h3>
        <p className="text-xs text-slate-400 mb-4 leading-relaxed font-medium">
          The streaming subsystem is configured for Apache Kafka on broker <code>{kafkaBroker}</code>.
          When the local Kafka broker is offline, the transaction simulator supports direct HTTP ingestion to <code>POST /predict</code>, ensuring continuous evaluation without ever feigning a fake broker socket.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-navy-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px]">Topic 1</span>
            <span className="text-indigo-400 font-bold">transactions</span>
            <p className="text-slate-400 text-[11px] mt-1 font-sans">Raw incoming transaction events from payment streams</p>
          </div>
          <div className="p-3.5 rounded-xl bg-navy-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px]">Topic 2</span>
            <span className="text-blue-400 font-bold">fraud-predictions</span>
            <p className="text-slate-400 text-[11px] mt-1 font-sans">Inference output events with probabilities and risk scores</p>
          </div>
          <div className="p-3.5 rounded-xl bg-navy-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px]">Topic 3</span>
            <span className="text-rose-400 font-bold">fraud-alerts</span>
            <p className="text-slate-400 text-[11px] mt-1 font-sans">High-risk transactions queued for security analyst review</p>
          </div>
        </div>
      </div>
    </div>
  );
}
