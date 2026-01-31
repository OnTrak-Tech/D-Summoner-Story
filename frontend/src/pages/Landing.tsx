import React from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../components/layout';

export const Landing: React.FC = () => {
    return (
        <Layout>
            {/* Hero Section */}
            <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
                {/* Background Effects */}
                <div className="absolute inset-0 bg-gradient-to-b from-purple-900/20 via-transparent to-cyan-900/20" />
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/30 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-600/30 rounded-full blur-3xl" />

                <div className="relative z-10 max-w-4xl mx-auto px-4 text-center">
                    {/* Main Headline */}
                    <h1 className="text-5xl md:text-7xl font-bold mb-6">
                        <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">
                            Your Gaming Story,
                        </span>
                        <br />
                        <span className="text-white">Told by AI</span>
                    </h1>

                    {/* Subtitle */}
                    <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
                        Get personalized insights, AI coaching, and shareable recaps of your
                        gaming journey across Riot Games and Fortnite.
                    </p>

                    {/* Platform Logos */}
                    <div className="flex justify-center items-center space-x-8 mb-10">
                        <div className="flex items-center space-x-2 text-gray-400">
                            <span className="text-3xl">🎮</span>
                            <span className="font-semibold">Riot Games</span>
                        </div>
                        <div className="w-px h-8 bg-gray-700" />
                        <div className="flex items-center space-x-2 text-gray-400">
                            <span className="text-3xl">🏆</span>
                            <span className="font-semibold">Fortnite</span>
                        </div>
                    </div>

                    {/* CTA Button */}
                    <Link
                        to="/auth"
                        className="inline-block px-8 py-4 bg-gradient-to-r from-purple-600 to-cyan-600 rounded-xl font-bold text-lg text-white hover:opacity-90 transition-all hover:scale-105 shadow-lg shadow-purple-500/25"
                    >
                        Get My Recap →
                    </Link>

                    {/* Social Proof */}
                    <p className="mt-6 text-sm text-gray-500">
                        Join 10,000+ gamers discovering their stats
                    </p>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 px-4">
                <div className="max-w-6xl mx-auto">
                    <h2 className="text-3xl font-bold text-center mb-12">
                        What You'll Discover
                    </h2>

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Feature 1 */}
                        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-purple-500/50 transition-all">
                            <div className="text-4xl mb-4">📊</div>
                            <h3 className="text-xl font-bold mb-2">Deep Stats</h3>
                            <p className="text-gray-400">
                                Comprehensive analytics across all your games, champions, and seasons.
                            </p>
                        </div>

                        {/* Feature 2 */}
                        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-cyan-500/50 transition-all">
                            <div className="text-4xl mb-4">🤖</div>
                            <h3 className="text-xl font-bold mb-2">AI Coach</h3>
                            <p className="text-gray-400">
                                Get personalized tips and insights powered by AI analysis of your gameplay.
                            </p>
                        </div>

                        {/* Feature 3 */}
                        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-pink-500/50 transition-all">
                            <div className="text-4xl mb-4">🎯</div>
                            <h3 className="text-xl font-bold mb-2">Shareable Recaps</h3>
                            <p className="text-gray-400">
                                Beautiful recap cards you can share with friends on social media.
                            </p>
                        </div>
                    </div>
                </div>
            </section>
        </Layout>
    );
};
