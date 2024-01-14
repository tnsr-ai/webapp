import { Button } from "@mantine/core";

export function Error() {
  return (
    <div className="w-full h-full">
      <div className="w-full flex justify-center">
        <p className="font-bold text-6xl">Oops!</p>
      </div>
      <div className="w-full flex justify-center mt-3">
        <p className="font-medium text-2xl tracking-wide">
          Something went wrong.
        </p>
      </div>
      <div className="w-full flex justify-center mt-6">
        <Button variant="outline" color="grape" size="xl" compact uppercase>
          RETRY
        </Button>
      </div>
    </div>
  );
}

export function TimeoutError() {
  return (
    <div className="w-full h-full">
      <div className="w-full flex justify-center">
        <p className="font-bold text-6xl">Too many requests!</p>
      </div>
      <div className="w-full flex justify-center mt-3">
        <p className="font-medium text-2xl tracking-wide">
          Please wait for sometime and try again.
        </p>
      </div>
    </div>
  );
}
