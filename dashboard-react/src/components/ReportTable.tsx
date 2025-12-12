import React from "react";
import { Card, CardHeader, CardBody, CardTitle } from "./Card";
import { Badge } from "./Badge";

export const ReportTable: React.FC<{
  reports: any[];
}> = ({ reports }) => (
  <Card>
    <CardHeader>
      <CardTitle>📊 Usage Reports</CardTitle>
    </CardHeader>
    <CardBody className="p-0">
      {reports.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <span className="text-5xl mb-4 block">📭</span>
          <p className="text-lg">No reports found</p>
          <p className="text-sm mt-2">
            Try adjusting your filters or check back later
          </p>
        </div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Device</th>
                <th>Usage</th>
                <th>Type</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r, idx) => (
                <tr key={idx}>
                  <td className="font-medium">{r.date}</td>
                  <td>{r.device}</td>
                  <td className="font-semibold text-emerald-600">{r.usage}</td>
                  <td>
                    <Badge variant="info">{r.type}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </CardBody>
  </Card>
);
