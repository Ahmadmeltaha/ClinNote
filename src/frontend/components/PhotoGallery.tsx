import { useState, useRef, useCallback } from 'react';

interface Photo {
  url: string;
  altText: string;
}

interface PhotoGalleryProps {
  photos: Array<Photo>;
  status: 'available' | 'sold';
}

function SoldBadge() {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <span className="-rotate-45 bg-black/60 text-white text-4xl font-bold px-10 py-3 rounded-md tracking-widest">
        SOLD
      </span>
    </div>
  );
}

export function PhotoGallery({ photos, status }: PhotoGalleryProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Empty guard – show placeholder and return early
  if (photos.length === 0) {
    return (
      <div className="bg-gray-200 flex items-center justify-center aspect-video rounded-lg">
        <span className="text-gray-500">No photos available</span>
      </div>
    );
  }

  // Single photo guard – no navigation controls at all
  if (photos.length === 1) {
    return (
      <div className="relative">
        <img
          src={photos[0].url}
          alt={photos[0].altText}
          className="w-full aspect-video object-cover rounded-lg"
        />
        {status === 'sold' && <SoldBadge />}
      </div>
    );
  }

  // Mobile scroll handler – derive active index from scroll position
  const handleScroll = useCallback(() => {
    if (scrollRef.current) {
      const idx = Math.round(
        scrollRef.current.scrollLeft / scrollRef.current.offsetWidth
      );
      setActiveIndex(idx);
    }
  }, []);

  return (
    <div>
      {/* Main photo area (desktop or mobile, mutually exclusive) */}
      <div className="relative">
        {/* Desktop: single main photo reflecting activeIndex */}
        <div className="hidden lg:block">
          <img
            src={photos[activeIndex].url}
            alt={photos[activeIndex].altText}
            className="w-full aspect-video object-cover rounded-lg"
          />
        </div>

        {/* Mobile: horizontal scroll-snap gallery */}
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="flex lg:hidden overflow-x-auto scroll-smooth snap-x snap-mandatory rounded-lg overflow-y-hidden"
          style={{ scrollSnapType: 'x mandatory' }}
        >
          {photos.map((photo, index) => (
            <div
              key={index}
              className="min-w-full flex-shrink-0 snap-start"
              style={{ scrollSnapAlign: 'start' }}
            >
              <img
                src={photo.url}
                alt={photo.altText}
                className="w-full aspect-video object-cover"
              />
            </div>
          ))}
        </div>

        {/* Sold badge overlay on main photo area */}
        {status === 'sold' && <SoldBadge />}
      </div>

      {/* Desktop: clickable thumbnail strip (hidden on mobile) */}
      <div className="hidden lg:flex gap-2 mt-3 overflow-x-auto">
        {photos.map((photo, index) => (
          <button
            key={index}
            type="button"
            onClick={() => setActiveIndex(index)}
            className={`w-16 h-16 flex-shrink-0 rounded overflow-hidden border-2 ${
              index === activeIndex ? 'border-blue-600' : 'border-transparent'
            }`}
          >
            <img
              src={photo.url}
              alt={photo.altText}
              className="w-full h-full object-cover"
            />
          </button>
        ))}
      </div>

      {/* Mobile: pagination dots (hidden on desktop) */}
      <div className="flex justify-center gap-2 mt-3 lg:hidden">
        {photos.map((_, index) => (
          <span
            key={index}
            className={`w-2 h-2 rounded-full ${
              index === activeIndex ? 'bg-gray-800' : 'bg-gray-300'
            }`}
          />
        ))}
      </div>
    </div>
  );
}