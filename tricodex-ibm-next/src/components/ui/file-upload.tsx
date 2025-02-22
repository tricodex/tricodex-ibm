import { cn } from "@/lib/utils";
import React, { useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload } from "lucide-react";

export const FileUpload = ({
  onChange,
}: {
  onChange?: (files: File[]) => void;
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (newFiles: File[]) => {
    setFiles((prevFiles) => [...prevFiles, ...newFiles]);
    onChange && onChange(newFiles);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const { getRootProps, isDragActive } = useDropzone({
    multiple: false,
    noClick: true,
    onDrop: handleFileChange,
    onDropRejected: (error) => {
      console.log(error);
    },
  });

  return (
    <div className="w-full" {...getRootProps()}>
      <div
        onClick={handleClick}
        className="p-8 block rounded-lg cursor-pointer w-full relative border-2 border-dashed border-muted-foreground/25 hover:border-muted-foreground/50 transition-colors"
      >
        <input
          ref={fileInputRef}
          id="file-upload-handle"
          type="file"
          onChange={(e) => handleFileChange(Array.from(e.target.files || []))}
          className="hidden"
        />
        
        <div className="flex flex-col items-center justify-center gap-4">
          <div className="p-4 bg-muted rounded-full">
            <Upload className="h-6 w-6 text-muted-foreground" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium">
              {isDragActive ? "Drop your file here" : "Upload your file"}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Drag and drop your files here or click to browse
            </p>
          </div>
        </div>

        {files.length > 0 && (
          <div className="mt-6 space-y-4">
            {files.map((file, idx) => (
              <div
                key={idx}
                className="bg-muted/50 rounded-lg p-4"
              >
                <div className="flex items-center justify-between gap-4">
                  <p className="text-sm font-medium truncate">
                    {file.name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
                <div className="flex items-center justify-between text-sm text-muted-foreground mt-2">
                  <p className="bg-muted px-2 py-1 rounded text-xs">
                    {file.type || 'Unknown type'}
                  </p>
                  <p className="text-xs">
                    Modified {new Date(file.lastModified).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};