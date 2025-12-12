import React from "react";
import { Card, CardHeader, CardBody, CardTitle } from "./Card";
import { Badge } from "./Badge";

export const TopConsumersTable: React.FC<{
  consumers: any[];
}> = ({ consumers }) => (
  <Card>
    <CardHeader>
      <CardTitle>🏆 Top Consumers</CardTitle>
    </CardHeader>
    <CardBody className="p-0">
      {consumers.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <span className="text-5xl mb-4 block">🎯</span>
          <p className="text-lg">No top consumers found</p>
          <p className="text-sm mt-2">
            Usage data will appear once devices are active
          </p>
        </div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Device</th>
                <th>Usage</th>
              </tr>
            </thead>
            <tbody>
              {consumers.map((c, idx) => (
                <tr key={idx}>
                  <td className="w-16">
                    {idx === 0 && <span className="text-xl">🥇</span>}
                    {idx === 1 && <span className="text-xl">🥈</span>}
                    {idx === 2 && <span className="text-xl">🥉</span>}
                    {idx > 2 && <Badge variant="neutral">#{idx + 1}</Badge>}
                  </td>
                  <td className="font-medium">{c.device}</td>
                  <td className="font-bold text-emerald-600">{c.usage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </CardBody>
  </Card>
);
