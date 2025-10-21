import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';

// Sample Button component for demonstration
const Button = ({ 
  primary = false, 
  size = 'medium', 
  label, 
  onClick,
  disabled = false,
  ...props 
}: {
  primary?: boolean;
  size?: 'small' | 'medium' | 'large';
  label: string;
  onClick?: () => void;
  disabled?: boolean;
}) => {
  const baseClasses = 'font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  const sizeClasses = {
    small: 'px-3 py-1.5 text-sm',
    medium: 'px-4 py-2 text-base',
    large: 'px-6 py-3 text-lg',
  };
  const colorClasses = primary
    ? 'bg-aqua-500 text-white hover:bg-aqua-600 focus:ring-aqua-500 disabled:bg-aqua-300'
    : 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500 disabled:bg-gray-100';

  return (
    <button
      type="button"
      className={`${baseClasses} ${sizeClasses[size]} ${colorClasses}`}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {label}
    </button>
  );
};

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A customizable button component with AquaChain branding and accessibility features.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    primary: {
      control: 'boolean',
      description: 'Primary button styling',
    },
    size: {
      control: { type: 'select' },
      options: ['small', 'medium', 'large'],
      description: 'Button size',
    },
    label: {
      control: 'text',
      description: 'Button text',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
    onClick: {
      action: 'clicked',
      description: 'Click handler',
    },
  },
  args: {
    onClick: action('button-click'),
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    primary: true,
    label: 'Get Started',
  },
};

export const Secondary: Story = {
  args: {
    primary: false,
    label: 'Learn More',
  },
};

export const Small: Story = {
  args: {
    size: 'small',
    label: 'Small Button',
  },
};

export const Large: Story = {
  args: {
    size: 'large',
    label: 'Large Button',
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    label: 'Disabled Button',
  },
};

// Accessibility test story
export const AccessibilityTest: Story = {
  args: {
    primary: true,
    label: 'Accessibility Test',
  },
  parameters: {
    a11y: {
      config: {
        rules: [
          {
            id: 'color-contrast',
            enabled: true,
          },
          {
            id: 'keyboard-navigation',
            enabled: true,
          },
        ],
      },
    },
  },
};