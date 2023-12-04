import Image from "next/image";
import React from "react";

function GradientBar() {
  return (
    <div className="h-[100%] lg:h-screen bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 bg-opacity-60 backdrop-blur-2xl background-animate flex justify-center items-center">
      <style>
        {`
            .background-animate {
              animation: animate-gradient 10s ease infinite;
              background-size: 400% 400%;
            }
            
            @keyframes animate-gradient {
              0% {
                background-position: 0 50%;
              }
              50% {
                background-position: 100% 50%;
              }
              100% {
                background-position: 0 50%;
              }
            }
          `}
      </style>
      <div className="">
        <div>
          <Image
            src="/assets/mainlogo_trimmed.png"
            alt="logo"
            className="w-[132px] lg:w-[186px] m-auto lg:pt-10 p-3"
            width={186}
            height={186}
          />
          <h1 className="text-center font-semibold text-3xl xl:text-4xl text-white hidden lg:block mb-6 tracking-tight">
            Welcome to tnsr.ai
          </h1>
          <h1 className="text-center font-normal text-xl xl:text-2xl text-white hidden lg:block px-4 tracking-tight">
            Login to unleash the full potential of your media content.
          </h1>
        </div>
      </div>
    </div>
  );
}

export default GradientBar;
