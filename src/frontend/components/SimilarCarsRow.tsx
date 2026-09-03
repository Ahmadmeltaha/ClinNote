import { Link } from 'react-router-dom';

interface CarSummary {
  id: string;
  make: string;
  model: string;
  year: number;
  price: number;
  mainPhotoUrl: string;
}

interface SimilarCarsRowProps {
  cars: Array<CarSummary>;
}

export function SimilarCarsRow({ cars }: SimilarCarsRowProps) {
  if (cars.length === 0) {
    return null;
  }

  return (
    <section>
      <h2 className="text-xl font-semibold mb-4 text-gray-900">Similar Cars</h2>
      <div className="flex overflow-x-auto gap-4 pb-4 -mx-4 px-4 scrollbar-thin scrollbar-thumb-gray-300">
        {cars.map((car) => (
          <Link
            key={car.id}
            to={`/cars/${car.id}`}
            className="flex-shrink-0 w-64 group"
          >
            <div className="rounded-lg overflow-hidden border border-gray-200 shadow-sm hover:shadow-md transition-shadow bg-white">
              <img
                className="w-full h-40 object-cover"
                src={car.mainPhotoUrl}
                alt={`${car.year} ${car.make} ${car.model}`}
              />
              <div className="p-3">
                <p className="text-sm text-gray-500">{car.year}</p>
                <p className="text-base font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                  {car.make} {car.model}
                </p>
                <p className="text-lg font-bold text-gray-900 mt-1">
                  ${car.price.toLocaleString()}
                </p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}