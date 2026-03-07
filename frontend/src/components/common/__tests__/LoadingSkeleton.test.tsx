/**
 * LoadingSkeleton Component Tests
 * 
 * Unit tests for LoadingSkeleton component.
 * Tests variants, count, animation, and predefined layouts.
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import {
  LoadingSkeleton,
  CardSkeleton,
  TableRowSkeleton,
  ChartSkeleton,
  KPICardSkeleton,
} from "../LoadingSkeleton";

describe("LoadingSkeleton", () => {
  describe("Basic Rendering", () => {
    it("renders single skeleton by default", () => {
      render(<LoadingSkeleton />);
      const skeleton = screen.getByRole("status");
      expect(skeleton).toBeInTheDocument();
    });

    it("has loading aria-label", () => {
      render(<LoadingSkeleton />);
      const skeleton = screen.getByRole("status");
      expect(skeleton).toHaveAttribute("aria-label", "Loading content");
    });

    it("has aria-live polite", () => {
      render(<LoadingSkeleton />);
      const skeleton = screen.getByRole("status");
      expect(skeleton).toHaveAttribute("aria-live", "polite");
    });
  });

  describe("Count", () => {
    it("renders single skeleton when count is 1", () => {
      render(<LoadingSkeleton count={1} />);
      const skeletons = screen.getAllByRole("status");
      expect(skeletons).toHaveLength(1);
    });

    it("renders multiple skeletons when count > 1", () => {
      render(<LoadingSkeleton count={3} />);
      const skeletons = screen.getAllByRole("status");
      expect(skeletons).toHaveLength(4); // 1 container + 3 elements
    });

    it("wraps multiple skeletons in space-y container", () => {
      const { container } = render(<LoadingSkeleton count={3} />);
      const wrapper = container.querySelector(".space-y-4");
      expect(wrapper).toBeInTheDocument();
    });
  });

  describe("Variants", () => {
    it("renders text variant", () => {
      const { container } = render(<LoadingSkeleton variant="text" />);
      const skeleton = container.querySelector(".rounded");
      expect(skeleton).toBeInTheDocument();
    });

    it("renders card variant by default", () => {
      const { container } = render(<LoadingSkeleton />);
      const skeleton = container.querySelector(".rounded-lg");
      expect(skeleton).toBeInTheDocument();
    });

    it("renders circle variant", () => {
      const { container } = render(<LoadingSkeleton variant="circle" />);
      const skeleton = container.querySelector(".rounded-full");
      expect(skeleton).toBeInTheDocument();
    });

    it("renders rectangle variant", () => {
      const { container } = render(<LoadingSkeleton variant="rectangle" />);
      const skeleton = container.querySelector(".rounded-lg");
      expect(skeleton).toBeInTheDocument();
    });
  });

  describe("Custom Dimensions", () => {
    it("applies custom width", () => {
      const { container } = render(<LoadingSkeleton width="200px" />);
      const skeleton = container.querySelector('[style*="width: 200px"]');
      expect(skeleton).toBeInTheDocument();
    });

    it("applies custom height", () => {
      const { container } = render(<LoadingSkeleton height="100px" />);
      const skeleton = container.querySelector('[style*="height: 100px"]');
      expect(skeleton).toBeInTheDocument();
    });

    it("applies both custom width and height", () => {
      const { container } = render(
        <LoadingSkeleton width="300px" height="150px" />
      );
      const skeleton = container.querySelector(
        '[style*="width: 300px"][style*="height: 150px"]'
      );
      expect(skeleton).toBeInTheDocument();
    });
  });

  describe("Animation", () => {
    it("has pulse animation by default", () => {
      const { container } = render(<LoadingSkeleton />);
      const skeleton = container.querySelector(".animate-pulse");
      expect(skeleton).toBeInTheDocument();
    });

    it("removes animation when animate is false", () => {
      const { container } = render(<LoadingSkeleton animate={false} />);
      const skeleton = container.querySelector(".animate-pulse");
      expect(skeleton).not.toBeInTheDocument();
    });
  });

  describe("Custom Styling", () => {
    it("applies custom className", () => {
      const { container } = render(<LoadingSkeleton className="custom-class" />);
      const skeleton = container.querySelector(".custom-class");
      expect(skeleton).toBeInTheDocument();
    });
  });

  describe("Dark Mode Support", () => {
    it("has dark mode classes", () => {
      const { container } = render(<LoadingSkeleton />);
      const skeleton = container.querySelector(".dark\\:bg-gray-700");
      expect(skeleton).toBeInTheDocument();
    });
  });
});

describe("CardSkeleton", () => {
  it("renders card skeleton with header and body", () => {
    const { container } = render(<CardSkeleton />);
    const card = container.querySelector(".bg-white");
    expect(card).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<CardSkeleton className="custom-card" />);
    const card = container.querySelector(".custom-card");
    expect(card).toBeInTheDocument();
  });
});

describe("TableRowSkeleton", () => {
  it("renders table row skeleton with default 5 columns", () => {
    render(<TableRowSkeleton />);
    const skeletons = screen.getAllByRole("status");
    expect(skeletons).toHaveLength(5);
  });

  it("renders custom number of columns", () => {
    render(<TableRowSkeleton columns={3} />);
    const skeletons = screen.getAllByRole("status");
    expect(skeletons).toHaveLength(3);
  });

  it("applies custom className", () => {
    const { container } = render(<TableRowSkeleton className="custom-row" />);
    const row = container.querySelector(".custom-row");
    expect(row).toBeInTheDocument();
  });
});

describe("ChartSkeleton", () => {
  it("renders chart skeleton with title and chart area", () => {
    render(<ChartSkeleton />);
    const skeletons = screen.getAllByRole("status");
    expect(skeletons.length).toBeGreaterThanOrEqual(2);
  });

  it("applies custom className", () => {
    const { container } = render(<ChartSkeleton className="custom-chart" />);
    const chart = container.querySelector(".custom-chart");
    expect(chart).toBeInTheDocument();
  });
});

describe("KPICardSkeleton", () => {
  it("renders KPI card skeleton with label, value, and trend", () => {
    const { container } = render(<KPICardSkeleton />);
    const card = container.querySelector(".bg-white");
    expect(card).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<KPICardSkeleton className="custom-kpi" />);
    const card = container.querySelector(".custom-kpi");
    expect(card).toBeInTheDocument();
  });
});
