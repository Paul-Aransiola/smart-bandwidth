import React from "react";

export const DeviceActions: React.FC<{
  device: any;
  onAction: (action: string) => void;
}> = ({ device, onAction }) => (
  <div className="device-actions">
    <button onClick={() => onAction("block")}>Block</button>
    <button onClick={() => onAction("unblock")}>Unblock</button>
    <button onClick={() => onAction("throttle")}>Throttle</button>
    <button onClick={() => onAction("unthrottle")}>Unthrottle</button>
    {/* Add modals/forms for reasons/limits as needed */}
  </div>
);
