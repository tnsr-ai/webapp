import { Button } from "@mantine/core";

export default function Error() {
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
