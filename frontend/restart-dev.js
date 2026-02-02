#!/usr/bin/env node

/**
 * Development Server Restart Script
 * Handles graceful restart with improved error handling
 */

const { spawn } = require('child_process');
const path = require('path');

console.log('🔄 Restarting AquaChain development servers...\n');

// Kill any existing processes on the ports
const killProcesses = async () => {
  const killCommands = [
    'taskkill /F /IM node.exe 2>nul || true',  // Windows
    'pkill -f "dev-server.js" 2>/dev/null || true',  // Unix
    'pkill -f "craco start" 2>/dev/null || true'     // Unix
  ];

  for (const cmd of killCommands) {
    try {
      await new Promise((resolve) => {
        const proc = spawn('cmd', ['/c', cmd], { shell: true, stdio: 'ignore' });
        proc.on('close', () => resolve());
        setTimeout(resolve, 1000); // Timeout after 1 second
      });
    } catch (error) {
      // Ignore errors - processes might not exist
    }
  }
};

const startServers = () => {
  console.log('✅ Starting development servers with fixes applied...\n');
  
  // Set environment variables to suppress warnings
  process.env.NODE_NO_WARNINGS = '1';
  process.env.SUPPRESS_NO_CONFIG_WARNING = 'true';
  
  // Start the development servers
  const npmStart = spawn('npm', ['run', 'start:full'], {
    cwd: process.cwd(),
    stdio: 'inherit',
    shell: true,
    env: {
      ...process.env,
      NODE_NO_WARNINGS: '1',
      SUPPRESS_NO_CONFIG_WARNING: 'true'
    }
  });

  npmStart.on('error', (error) => {
    console.error('❌ Failed to start development servers:', error);
    process.exit(1);
  });

  npmStart.on('close', (code) => {
    if (code !== 0) {
      console.error(`❌ Development servers exited with code ${code}`);
      process.exit(code);
    }
  });

  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down development servers...');
    npmStart.kill('SIGINT');
    process.exit(0);
  });
};

// Main execution
(async () => {
  try {
    await killProcesses();
    setTimeout(startServers, 2000); // Wait 2 seconds before starting
  } catch (error) {
    console.error('❌ Error during restart:', error);
    process.exit(1);
  }
})();