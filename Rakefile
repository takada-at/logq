# coding: utf-8
require 'rake/clean'

TESTDIR = "build/ext_test"
GTESTDIR = "/usr/local/lib/gtest"
PYTHONPATH = "~/include/python2.7/"
includes = "-I#{GTESTDIR} -I logq/src/ -I #{PYTHONPATH}"
directory TESTDIR

SrcFiles = FileList["build/extest/*"]
testsrcs = FileList["logq/src/test/*.cc"]


task :default => [:ext_test]
task :ext_test => TESTDIR do
    testsrcs.each do |src|
        out = src.pathmap('%n')
        sh "g++ -isystem #{GTESTDIR}/include #{includes} -pthread #{src} #{GTESTDIR}/lib/libgtest.a -o #{TESTDIR}/#{out}"
        sh "#{TESTDIR}/#{out}"
    end
end

rule 
