import React from 'react';

import { Platform } from '../config/platforms';

interface OnTrakAICoachLandingProps {
  onGetStarted: (platform?: Platform) => void;
}

export const OnTrakAICoachLanding: React.FC<OnTrakAICoachLandingProps> = ({ onGetStarted }) => {
  return (
    // Background updated to brand-dark
    <div className="min-h-screen bg-brand-dark text-[#E5E5E5] font-sans selection:bg-brand-vibrant selection:text-white">
      {/* Navigation - Glassmorphism with your brand colors */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-4 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-brand-secondary/80 backdrop-blur-xl border border-brand-vibrant/20 rounded-2xl px-8 py-4 flex items-center justify-between shadow-2xl">
            <div className="flex items-center space-x-12">
              <div className="flex items-center space-x-3 group cursor-pointer">
                {/* Logo using brand-deep */}
                <div className="w-10 h-10 bg-brand-deep rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(167,55,40,0.4)]">
                  <span className="text-white font-black">G</span>
                </div>
                <span className="text-white font-black text-2xl tracking-tighter uppercase">
                  GameWrapped
                </span>
              </div>

              <div className="hidden lg:flex items-center space-x-10">
                {['Home', 'Platforms', 'About', 'Contact'].map((item) => (
                  <a
                    key={item}
                    href={`#${item.toLowerCase()}`}
                    className="text-xs uppercase tracking-[0.2em] font-black text-gray-400 hover:text-brand-vibrant transition-all duration-300"
                  >
                    {item}
                  </a>
                ))}
              </div>
            </div>

            {/* Primary Action Button using brand-vibrant */}
            <button
              onClick={() => onGetStarted()}
              className="bg-brand-vibrant text-white px-8 py-2.5 rounded-lg font-black uppercase text-xs tracking-widest hover:bg-brand-deep transition-all duration-300 transform active:scale-95 shadow-lg shadow-brand-vibrant/20"
            >
              Sign In
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section - Asymmetric Alignment inspired by your sample */}
      <section className="relative min-h-screen flex items-center pt-24 overflow-hidden px-8">
        {/* Glow Effect using Red/Orange mix */}
        <div className="absolute top-1/2 -right-40 transform -translate-y-1/2 w-[800px] h-[800px] pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-vibrant/20 to-brand-deep/5 rounded-full blur-[150px] animate-pulse"></div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto grid lg:grid-cols-2 gap-20 items-center">
          <div className="text-left">
            <div className="inline-block px-4 py-1 mb-8 border border-brand-vibrant/40 bg-brand-vibrant/5 rounded-md">
              <span className="text-brand-vibrant text-[10px] font-black tracking-[0.4em] uppercase">
                AI-Driven Tactical Analysis
              </span>
            </div>

            <h1 className="text-7xl md:text-9xl font-black tracking-tighter leading-[0.8] uppercase mb-10 italic">
              Discover <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-vibrant to-brand-deep">
                Your Story
              </span>{' '}
              <br />
              With AI
            </h1>

            <p className="text-gray-400 text-lg md:text-xl max-w-lg leading-relaxed mb-12 font-medium border-l-2 border-brand-vibrant/30 pl-6">
              Your raw match data contains patterns only AI can see. We decode your League of
              Legends legacy into professional coaching stories.
            </p>

            <div className="flex flex-wrap gap-6">
              <button
                onClick={() => onGetStarted()}
                className="bg-brand-vibrant text-white px-12 py-5 rounded-sm font-black uppercase tracking-tighter hover:bg-brand-deep transition-all transform hover:-translate-y-1 shadow-xl shadow-brand-vibrant/20"
              >
                Start Your Journey
              </button>
              <button className="border-2 border-white/10 text-white px-12 py-5 rounded-sm font-black uppercase tracking-tighter hover:bg-white hover:text-black transition-all">
                Watch Demo
              </button>
            </div>
          </div>

          {/* Visual Showcase - Bento Box style highlight */}
          <div className="relative hidden lg:block group">
            <div className="relative z-10 rounded-3xl overflow-hidden border border-white/5 bg-brand-secondary p-3 shadow-2xl">
              <div className="aspect-[4/5] bg-gradient-to-t from-brand-dark to-brand-deep/20 rounded-2xl flex items-center justify-center relative overflow-hidden">
                {/* This is where your slow-moving hero image goes */}
                <span className="text-9xl group-hover:scale-110 transition-transform duration-1000">
                  🛡️
                </span>

                {/* Dynamic Corner Accents in brand-vibrant */}
                <div className="absolute bottom-6 left-6 text-left">
                  <p className="text-[10px] font-black uppercase tracking-widest text-brand-vibrant">
                    Latest Match
                  </p>
                  <p className="text-2xl font-black uppercase italic">Victory</p>
                </div>
              </div>
            </div>
            {/* Decorative Frame */}
            <div className="absolute -top-6 -right-6 w-32 h-32 border-t-4 border-r-4 border-brand-vibrant rounded-tr-3xl opacity-40 group-hover:opacity-100 transition-opacity"></div>
          </div>
        </div>
      </section>
    </div>
  );
};
