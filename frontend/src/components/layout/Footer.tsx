import React from 'react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
    return (
        <footer className="bg-black/60 border-t border-white/10 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
                    {/* Logo */}
                    <div className="flex items-center space-x-2">
                        <span className="text-xl"></span>
                        <span className="text-lg font-bold text-gray-400">GamerRecap</span>
                    </div>

                    {/* Links */}
                    <div className="flex space-x-6 text-sm text-gray-400">
                        <Link to="/about" className="hover:text-white transition-colors">
                            About
                        </Link>
                        <Link to="/privacy" className="hover:text-white transition-colors">
                            Privacy
                        </Link>
                        <Link to="/terms" className="hover:text-white transition-colors">
                            Terms
                        </Link>
                        <a
                            href="https://twitter.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-white transition-colors"
                        >
                            Twitter
                        </a>
                    </div>

                    {/* Copyright */}
                    <p className="text-sm text-gray-500">
                        © {new Date().getFullYear()} GamerRecap. All rights reserved.
                    </p>
                </div>
            </div>
        </footer>
    );
};
