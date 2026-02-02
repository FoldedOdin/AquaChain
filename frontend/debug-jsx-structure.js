#!/usr/bin/env node

/**
 * Debug script to find exact JSX structure issues
 */

const fs = require('fs');
const path = require('path');

const modalPath = path.join(__dirname, 'src/components/Dashboard/AddDeviceModal.tsx');
const content = fs.readFileSync(modalPath, 'utf8');

console.log('🔍 Analyzing JSX Structure...\n');

const lines = content.split('\n');
let openDivs = 0;
let closeDivs = 0;
let balance = 0;

console.log('Line | Balance | Content');
console.log('-----|---------|--------');

lines.forEach((line, index) => {
  const lineNum = (index + 1).toString().padStart(3, ' ');
  const openMatches = (line.match(/<div/g) || []).length;
  const closeMatches = (line.match(/<\/div>/g) || []).length;
  
  openDivs += openMatches;
  closeDivs += closeMatches;
  balance += openMatches - closeMatches;
  
  if (openMatches > 0 || closeMatches > 0) {
    const balanceStr = balance.toString().padStart(7, ' ');
    const trimmedLine = line.trim().substring(0, 60);
    console.log(`${lineNum} | ${balanceStr} | ${trimmedLine}`);
  }
});

console.log('\n📊 Summary:');
console.log(`Total opening <div> tags: ${openDivs}`);
console.log(`Total closing </div> tags: ${closeDivs}`);
console.log(`Final balance: ${balance}`);

if (balance !== 0) {
  console.log(`\n❌ JSX Structure Issue: ${balance > 0 ? 'Missing closing' : 'Extra closing'} div tags`);
} else {
  console.log('\n✅ JSX Structure is balanced');
}