import React from 'react';

interface NavbarProps {
  onGetStarted: () => void;
}

export const ImmersiveNavbar: React.FC<NavbarProps> = ({ onGetStarted }) => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-4 py-6">
      <div className="max-w-7xl mx-auto">
        {/* Container: Changed to your brand dark #1A0F0E with an orange-tinted border */}
        <div className="bg-[#1A0F0E]/80 backdrop-blur-2xl border border-[#DF643F]/20 rounded-2xl px-6 py-3 shadow-2xl">
          <div className="flex items-center justify-between">
            {/* Left Group: Logo + Left-aligned Links */}
            <div className="flex items-center space-x-12">
              {/* Logo: Using Deep Red #A73728 */}
              <div className="flex items-center space-x-3 group cursor-pointer">
                <div className="w-10 h-10 bg-[#A73728] rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(167,55,40,0.4)] transition-transform group-hover:scale-110">
                  <span className="text-white font-black text-xl italic">O</span>
                </div>
                <span className="text-white font-black text-2xl tracking-tighter uppercase italic">
                  OnTrak<span className="text-[#DF643F]">AI</span>
                </span>
              </div>

              {/* Navigation Links: Now Left-aligned next to logo */}
              <div className="hidden lg:flex items-center space-x-8">
                {['Home', 'Platforms', 'About', 'Contact'].map((item) => (
                  <a
                    key={item}
                    href={`#${item.toLowerCase()}`}
                    className="text-[11px] uppercase tracking-[0.25em] font-black text-gray-400 hover:text-[#DF643F] transition-all duration-300 relative group"
                  >
                    {item}
                    {/* Hover Underline using Vibrant Orange */}
                    <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-[#DF643F] transition-all duration-300 group-hover:w-full"></span>
                  </a>
                ))}
              </div>
            </div>

            {/* Right Group: Sign In / CTA */}
            <div className="flex items-center space-x-4">
              <button className="hidden sm:block text-gray-400 hover:text-white text-xs font-black uppercase tracking-widest transition-colors">
                Sign In
              </button>
              <button
                onClick={onGetStarted}
                className="bg-[#DF643F] text-white px-8 py-3 rounded-lg font-black uppercase text-xs tracking-widest hover:bg-[#A73728] transition-all duration-300 transform active:scale-95 shadow-lg shadow-[#DF643F]/20"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};
