"use client";
import React, { useState } from "react";

const AppBar = () => {

  return (
    <div className="w-full h-full">
      <div className="w-full bg-white flex flex-row items-center">
        <div className="w-full flex justify-center items-center lg:hidden p-2">
          <h1 className="text-2xl font-bold">tnsr.ai</h1>
        </div>
      </div>
    </div>
  );
};

export default AppBar;
