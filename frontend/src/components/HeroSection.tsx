import React, { useEffect, useState } from 'react';

interface HeroSectionProps {
  onGetStarted: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onGetStarted }) => {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Video Background */}
      <div className="absolute inset-0 z-0">
        <div className="w-full h-full bg-gradient-to-br from-[#0D1117] via-[#0B0E11] to-[#0D1117]">
          {/* Animated gaming elements */}
          <div className="absolute inset-0">
            <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-[#00FF85]/5 rounded-full blur-3xl animate-pulse" />
            <div
              className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-400/5 rounded-full blur-3xl animate-pulse"
              style={{ animationDelay: '2s' }}
            />
            <div
              className="absolute top-1/2 left-1/2 w-48 h-48 bg-purple-500/5 rounded-full blur-3xl animate-pulse"
              style={{ animationDelay: '4s' }}
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 text-center px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
        {/* Kinetic Typography */}
        <div className="mb-6 sm:mb-8">
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-black tracking-tight mb-2 sm:mb-4">
            <span
              className="inline-block text-[#E0E0E0] hover:text-[#00FF85] transition-all duration-500 transform hover:scale-110"
              style={{ transform: `translateY(${scrollY * 0.1}px)` }}
            >
              YOUR
            </span>
            <span className="mx-2 sm:mx-4 text-[#00FF85]">•</span>
            <span
              className="inline-block text-[#E0E0E0] hover:text-cyan-400 transition-all duration-500 transform hover:scale-110"
              style={{ transform: `translateY(${scrollY * -0.1}px)` }}
            >
              STORY
            </span>
          </h1>
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black tracking-tight">
            <span
              className="bg-gradient-to-r from-[#00FF85] via-cyan-400 to-purple-400 bg-clip-text text-transparent"
              style={{ transform: `translateX(${scrollY * 0.05}px)` }}
            >
              REWRITTEN BY AI
            </span>
          </h2>
        </div>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl md:text-2xl text-[#E0E0E0]/80 mb-8 sm:mb-12 max-w-3xl mx-auto leading-relaxed px-4">
          Transform your gaming data into cinematic stories. Advanced AI analyzes your gameplay
          across multiple platforms to create your personalized gaming wrapped.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 sm:gap-6 justify-center items-center px-4">
          <button
            onClick={onGetStarted}
            className="group bg-gradient-to-r from-[#00FF85] to-cyan-400 text-black px-8 sm:px-12 py-3 sm:py-4 rounded-2xl font-bold text-base sm:text-lg hover:shadow-2xl hover:shadow-[#00FF85]/25 transition-all duration-300 transform hover:scale-105 w-full sm:w-auto"
          >
            <span className="flex items-center justify-center gap-3">
              Start Your Journey
              <svg
                className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </span>
          </button>

          <button className="text-[#E0E0E0] border border-[#E0E0E0]/20 px-8 sm:px-12 py-3 sm:py-4 rounded-2xl font-bold text-base sm:text-lg hover:border-[#00FF85] hover:text-[#00FF85] transition-all duration-300 backdrop-blur-sm w-full sm:w-auto">
            Watch Demo
          </button>
        </div>

        {/* Stats */}
        <div className="mt-12 sm:mt-20 grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8 max-w-4xl mx-auto px-4">
          <div className="text-center">
            <div className="text-3xl sm:text-4xl font-black text-[#00FF85] mb-2">1M+</div>
            <div className="text-[#E0E0E0]/60 font-medium text-sm sm:text-base">
              Stories Created
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl sm:text-4xl font-black text-cyan-400 mb-2">50+</div>
            <div className="text-[#E0E0E0]/60 font-medium text-sm sm:text-base">
              Games Supported
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl sm:text-4xl font-black text-purple-400 mb-2">99.9%</div>
            <div className="text-[#E0E0E0]/60 font-medium text-sm sm:text-base">Accuracy Rate</div>
          </div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 border-2 border-[#E0E0E0]/30 rounded-full flex justify-center">
          <div className="w-1 h-3 bg-[#00FF85] rounded-full mt-2 animate-pulse" />
        </div>
      </div>
    </section>
  );
};
