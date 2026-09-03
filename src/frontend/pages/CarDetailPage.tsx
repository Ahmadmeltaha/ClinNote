import { useParams, Link } from 'react-router-dom';
import { useCarDetail } from '@/frontend/hooks/useCarDetail';
import { PhotoGallery } from '@/frontend/components/PhotoGallery';
import { SimilarCarsRow } from '@/frontend/components/SimilarCarsRow';

export function CarDetailPage() {
  const { id: carId } = useParams<{ id: string }>();
  const { data, loading, error } = useCarDetail(carId!);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 rounded-full border-4 border-gray-200 border-t-blue-600 animate-spin" />
      </div>
    );
  }

  // Error / not-found state
  if (error !== null || (data === null && !loading)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Car not found.</h1>
        <Link
          to="/"
          className="text-blue-600 hover:underline font-medium"
        >
          ← Back to catalog
        </Link>
      </div>
    );
  }

  const isSold = data!.status === 'sold';
  const disabledClasses = isSold
    ? 'opacity-50 pointer-events-none cursor-not-allowed'
    : '';

  const actionButtons = (
    <>
      <button
        type="button"
        className={`px-6 py-3 rounded-lg font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors ${disabledClasses}`}
      >
        Book Test Drive
      </button>
      <button
        type="button"
        className={`px-6 py-3 rounded-lg font-semibold text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors ${disabledClasses}`}
      >
        Send Inquiry
      </button>
    </>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 pb-28 lg:pb-8">
      {/* Main grid: gallery left, details right */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Left column — Photo Gallery */}
        <div className="lg:col-span-3">
          <PhotoGallery photos={data!.photos} status={data!.status} />
        </div>

        {/* Right column — Specs, Price, Description, Inline Action Buttons */}
        <div className="lg:col-span-2">
          {/* Specs grid */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-3">
            <div>
              <dt className="text-sm text-gray-500">Make</dt>
              <dd className="text-base font-medium text-gray-900">{data!.make}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Model</dt>
              <dd className="text-base font-medium text-gray-900">{data!.model}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Year</dt>
              <dd className="text-base font-medium text-gray-900">{data!.year}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Mileage</dt>
              <dd className="text-base font-medium text-gray-900">{data!.mileage.toLocaleString()} mi</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Fuel</dt>
              <dd className="text-base font-medium text-gray-900">{data!.fuel}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Transmission</dt>
              <dd className="text-base font-medium text-gray-900">{data!.transmission}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Color</dt>
              <dd className="text-base font-medium text-gray-900">{data!.color}</dd>
            </div>
          </div>

          {/* Price */}
          <p className="text-3xl font-bold text-gray-900 mt-6">
            ${data!.price.toLocaleString()}
          </p>

          {/* Description */}
          <div className="mt-6 prose prose-gray max-w-none">
            <p>{data!.description}</p>
          </div>

          {/* Desktop inline action buttons */}
          <div className="hidden lg:flex gap-4 mt-8">
            {actionButtons}
          </div>
        </div>
      </div>

      {/* Similar Cars */}
      <div className="mt-12">
        <SimilarCarsRow cars={data!.similarCars} />
      </div>

      {/* Mobile sticky bottom action bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)] p-4 flex gap-4 lg:hidden z-50">
        <div className="flex-1">
          <button
            type="button"
            className={`w-full px-6 py-3 rounded-lg font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors ${disabledClasses}`}
          >
            Book Test Drive
          </button>
        </div>
        <div className="flex-1">
          <button
            type="button"
            className={`w-full px-6 py-3 rounded-lg font-semibold text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors ${disabledClasses}`}
          >
            Send Inquiry
          </button>
        </div>
      </div>
    </div>
  );
}