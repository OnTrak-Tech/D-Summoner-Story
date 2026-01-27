import React, { useState, useEffect } from 'react';

const GAMING_IMAGES = [
  'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1920&h=1080&fit=crop&crop=center',
  'https://images.unsplash.com/photo-1511512578047-dfb367046420?w=1920&h=1080&fit=crop&crop=center',
  'https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?w=1920&h=1080&fit=crop&crop=center',
  'https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=1920&h=1080&fit=crop&crop=center',
  'https://images.unsplash.com/photo-1560253023-3ec5d502959f?w=1920&h=1080&fit=crop&crop=center'
];

export const GamingBackground: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % GAMING_IMAGES.length);
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {GAMING_IMAGES.map((image, index) => (
        <div
          key={image}
          className={`absolute inset-0 transition-opacity duration-1000 ${
            index === currentIndex ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <img
            src={image}
            alt="Gaming background"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-black/40" />
        </div>
      ))}
    </div>
  );
};